"""Routes for complaint CRUD operations - HTTP only, no business logic."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.metrics import rate_limit_exceeded
from app.models.complaint import Category, Priority, Status
from app.providers.triage import get_triage_provider
from app.schemas.complaint import (
    ComplaintCreate,
    ComplaintListResponse,
    ComplaintResponse,
    ComplaintStatusUpdate,
)
from app.schemas.errors import StateTransitionError
from app.services.complaint_service import ComplaintService
from app.services.redis_service import RedisService

router = APIRouter(prefix="/api/complaints", tags=["complaints"])
logger = get_logger(__name__)


def get_complaint_service(
    db: Session = Depends(get_db),
) -> ComplaintService:
    """Dependency to get complaint service instance."""
    triage_provider = get_triage_provider()
    redis_service = RedisService()
    return ComplaintService(db, triage_provider, redis_service)


@router.post(
    "",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Bad request - validation error"},
        429: {"description": "Rate limit exceeded"},
    },
)
def create_complaint(
    complaint: ComplaintCreate,
    request: Request,
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintResponse:
    """
    Create a new complaint.
    
    Validates input, performs triage (with caching and fallback),
    persists complaint, and returns 201.
    
    Rate limited per client IP.
    """
    # Rate limiting
    from app.core.config import settings

    if settings.RATE_LIMIT_ENABLED:
        client_ip = request.client.host if request.client else "unknown"
        redis_service = RedisService()
        
        allowed, retry_after = redis_service.check_rate_limit(
            client_ip,
            limit=settings.RATE_LIMIT_PER_MINUTE,
            window=60,
        )
        
        if not allowed:
            rate_limit_exceeded.labels(client_ip=client_ip).inc()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(retry_after)},
            )

    # Create complaint (always returns 201, never 500 due to fallback)
    return service.create_complaint(complaint)


@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    responses={
        404: {"description": "Complaint not found"},
    },
)
def get_complaint(
    complaint_id: UUID,
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintResponse:
    """Get a complaint by ID."""
    complaint = service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint {complaint_id} not found",
        )
    return complaint


@router.get(
    "",
    response_model=ComplaintListResponse,
)
def list_complaints(
    category: Category | None = Query(None, description="Filter by category"),
    priority: Priority | None = Query(None, description="Filter by priority"),
    complaint_status: Status | None = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintListResponse:
    """
    List complaints with optional filtering and pagination.
    
    Query parameters:
    - category: Filter by category
    - priority: Filter by priority
    - status: Filter by status
    - page: Page number (default 1)
    - page_size: Items per page (default 20, max 100)
    """
    return service.list_complaints(
        category=category,
        priority=priority,
        status=complaint_status,
        page=page,
        page_size=page_size,
    )


@router.patch(
    "/{complaint_id}/status",
    response_model=ComplaintResponse,
    responses={
        404: {"description": "Complaint not found"},
        409: {"description": "Invalid state transition"},
    },
)
def update_complaint_status(
    complaint_id: UUID,
    status_update: ComplaintStatusUpdate,
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintResponse:
    """
    Update complaint status.
    
    Enforces state machine transitions:
    - open -> in_progress, rejected
    - in_progress -> resolved, rejected
    - resolved -> (terminal, no transitions)
    - rejected -> (terminal, no transitions)
    
    Returns 409 with transition error message if invalid.
    """
    result, error = service.update_complaint_status(
        complaint_id,
        status_update.status,
    )
    
    if result is None and error is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint {complaint_id} not found",
        )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error,
        )
    
    return result  # type: ignore[return-value]
