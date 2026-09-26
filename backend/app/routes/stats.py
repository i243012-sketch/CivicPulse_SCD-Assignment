"""Routes for statistics endpoint - HTTP only."""
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.providers.triage import get_triage_provider
from app.schemas.complaint import StatsResponse
from app.services.complaint_service import ComplaintService
from app.services.redis_service import RedisService

router = APIRouter(prefix="/api", tags=["stats"])


def get_complaint_service(db: Session = Depends(get_db)) -> ComplaintService:
    """Dependency to get complaint service instance."""
    triage_provider = get_triage_provider()
    redis_service = RedisService()
    return ComplaintService(db, triage_provider, redis_service)


@router.get("/stats", response_model=StatsResponse)
def get_stats(
    response: Response,
    service: ComplaintService = Depends(get_complaint_service),
) -> StatsResponse:
    """
    Get aggregated complaint statistics.
    
    Returns counts grouped by category and priority.
    
    Response is cached in Redis for 30 seconds.
    Cache is invalidated immediately on any complaint write operation.
    
    Response header X-Cache indicates HIT or MISS.
    """
    stats, cache_hit = service.get_stats()
    
    # Set cache header
    response.headers["X-Cache"] = "HIT" if cache_hit else "MISS"
    
    return stats
