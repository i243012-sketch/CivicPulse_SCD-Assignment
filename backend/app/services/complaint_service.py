"""Business logic service for complaint operations."""
import json
import time
from collections import deque
from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.metrics import (
    triage_cache_hit,
    triage_cache_miss,
    triage_fallback_count,
    triage_latency,
    stats_cache_hit,
    stats_cache_miss,
)
from app.models.complaint import Category, Complaint, Priority, Status, is_valid_transition
from app.providers.triage import TriageProvider
from app.repositories.complaint_repository import ComplaintRepository
from app.schemas.complaint import (
    CategoryStats,
    ComplaintCreate,
    ComplaintListResponse,
    ComplaintResponse,
    PriorityStats,
    StatsResponse,
)
from app.schemas.triage import TriageOutcome, TriageResult
from app.services.redis_service import RedisService

logger = get_logger(__name__)


class ComplaintService:
    """Service layer for complaint business logic."""

    # Track last 20 triage outcomes in memory
    _recent_outcomes: deque[TriageOutcome] = deque(maxlen=20)

    def __init__(
        self,
        db: Session,
        triage_provider: TriageProvider,
        redis_service: RedisService,
    ) -> None:
        """
        Initialize complaint service.
        
        Args:
            db: Database session
            triage_provider: Triage provider instance
            redis_service: Redis service instance
        """
        self.repository = ComplaintRepository(db)
        self.triage_provider = triage_provider
        self.redis = redis_service

    def create_complaint(self, complaint_data: ComplaintCreate) -> ComplaintResponse:
        """
        Create a new complaint with triage.
        
        Business logic:
        1. Check cache for triage result (by content hash)
        2. If miss, call triage provider and cache result
        3. Create complaint with triage results
        4. Invalidate stats cache
        
        Args:
            complaint_data: Validated complaint creation data
            
        Returns:
            Created complaint response
        """
        # Compute content hash for cache key
        content_hash = RedisService.compute_content_hash(
            complaint_data.text,
            complaint_data.location,
        )
        cache_key = f"triage:{content_hash}"

        # Try to get from cache
        cached = self.redis.get(cache_key)
        start_time = time.time()
        fallback = False
        triaged_by = self.triage_provider.name

        if cached:
            # Cache hit - restore full cached outcome
            triage_cache_hit.inc()
            cached_data = json.loads(cached)
            triage_result = TriageResult(**cached_data["result"])
            triaged_by = cached_data["triaged_by"]  # Original provider name
            latency_ms = 0  # Cache hit is instant
            logger.info(
                "Triage cache hit",
                extra={"extra_fields": {"content_hash": content_hash, "original_provider": triaged_by}},
            )
        else:
            # Cache miss - call provider
            triage_cache_miss.inc()
            
            try:
                triage_result = self.triage_provider.triage(
                    complaint_data.text,
                    complaint_data.location,
                )
                
                # Check if fallback occurred (provider name changed)
                if self.triage_provider.name == "llm:groq" and "rules" in triaged_by:
                    fallback = True
                    triaged_by = "rules:fallback"
                    triage_fallback_count.labels(
                        provider=self.triage_provider.name,
                        reason="llm_failure",
                    ).inc()
                    
            except Exception as e:
                # Fallback on any exception
                logger.warning(
                    "Triage provider failed, using fallback",
                    extra={"extra_fields": {"error": str(e), "provider": triaged_by}},
                )
                fallback = True
                triaged_by = "rules:fallback"
                triage_fallback_count.labels(
                    provider=self.triage_provider.name,
                    reason="exception",
                ).inc()
                
                # Use rules as fallback
                from app.providers.triage.rules import RuleBasedTriage
                fallback_provider = RuleBasedTriage()
                triage_result = fallback_provider.triage(
                    complaint_data.text,
                    complaint_data.location,
                )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Cache the result WITH the provider name
            cache_data = {
                "result": json.loads(triage_result.model_dump_json()),
                "triaged_by": triaged_by,
            }
            self.redis.set(
                cache_key,
                json.dumps(cache_data),
                ttl=settings.REDIS_CACHE_TTL_TRIAGE,
            )

        # Record metrics
        triage_latency.labels(provider=self.triage_provider.name).observe(latency_ms)

        # Track outcome
        outcome = TriageOutcome(
            provider=triaged_by,
            latency_ms=latency_ms,
            fallback=fallback,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._recent_outcomes.append(outcome)

        # Create complaint model
        complaint = Complaint(
            text=complaint_data.text,
            location=complaint_data.location,
            reporter_contact=complaint_data.reporter_contact,
            category=triage_result.category,
            priority=triage_result.priority,
            status=Status.OPEN,
            ai_summary=triage_result.summary,
            triaged_by=triaged_by,
            triage_latency_ms=latency_ms,
        )

        # Persist to database
        created = self.repository.create(complaint)

        # Invalidate stats cache
        self.redis.delete("stats:aggregated")

        return ComplaintResponse.model_validate(created)

    def get_complaint(self, complaint_id: UUID) -> ComplaintResponse | None:
        """
        Get a complaint by ID.
        
        Args:
            complaint_id: UUID of complaint
            
        Returns:
            Complaint response if found, None otherwise
        """
        complaint = self.repository.get_by_id(complaint_id)
        if not complaint:
            return None
        return ComplaintResponse.model_validate(complaint)

    def list_complaints(
        self,
        category: Category | None = None,
        priority: Priority | None = None,
        status: Status | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ComplaintListResponse:
        """
        List complaints with filtering and pagination.
        
        Args:
            category: Optional category filter
            priority: Optional priority filter
            status: Optional status filter
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            Paginated list of complaints
        """
        complaints, total = self.repository.get_all(
            category=category,
            priority=priority,
            status=status,
            page=page,
            page_size=page_size,
        )

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return ComplaintListResponse(
            items=[ComplaintResponse.model_validate(c) for c in complaints],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def update_complaint_status(
        self,
        complaint_id: UUID,
        new_status: Status,
    ) -> tuple[ComplaintResponse | None, str | None]:
        """
        Update complaint status with state machine validation.
        
        Args:
            complaint_id: UUID of complaint
            new_status: New status to transition to
            
        Returns:
            Tuple of (updated complaint or None, error message or None)
        """
        # Get complaint
        complaint = self.repository.get_by_id(complaint_id)
        if not complaint:
            return None, None

        # Validate transition
        if not is_valid_transition(complaint.status, new_status):
            error_msg = (
                f"Cannot transition from '{complaint.status.value}' to '{new_status.value}'"
            )
            return None, error_msg

        # Update status
        updated = self.repository.update_status(complaint, new_status)

        # Invalidate stats cache
        self.redis.delete("stats:aggregated")

        return ComplaintResponse.model_validate(updated), None

    def get_stats(self) -> tuple[StatsResponse, bool]:
        """
        Get aggregated statistics with Redis caching.
        
        Returns:
            Tuple of (stats response, cache_hit boolean)
        """
        cache_key = "stats:aggregated"
        
        # Try cache first
        cached = self.redis.get(cache_key)
        if cached:
            stats_cache_hit.inc()
            return StatsResponse(**json.loads(cached)), True

        # Cache miss - compute from database
        stats_cache_miss.inc()

        category_data = self.repository.get_stats_by_category()
        priority_data = self.repository.get_stats_by_priority()
        total = self.repository.get_total_count()

        # Build response
        stats = StatsResponse(
            by_category=[
                CategoryStats(category=cat, count=count)
                for cat, count in category_data
            ],
            by_priority=[
                PriorityStats(priority=pri, count=count)
                for pri, count in priority_data
            ],
            total_complaints=total,
        )

        # Cache result
        self.redis.set(
            cache_key,
            stats.model_dump_json(),
            ttl=settings.REDIS_CACHE_TTL_STATS,
        )

        return stats, False

    @classmethod
    def get_recent_triage_outcomes(cls) -> list[TriageOutcome]:
        """
        Get recent triage outcomes for metadata endpoint.
        
        Returns:
            List of up to 20 most recent triage outcomes
        """
        return list(cls._recent_outcomes)
