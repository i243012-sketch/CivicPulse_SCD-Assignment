"""Routes for meta/system endpoints - HTTP only."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.schemas.meta import HealthResponse, ProvidersResponse, ReadyResponse
from app.services.complaint_service import ComplaintService
from app.services.redis_service import RedisService

router = APIRouter(prefix="/api/meta", tags=["meta"])


@router.get("/providers", response_model=ProvidersResponse)
def get_providers() -> ProvidersResponse:
    """
    Get active triage provider and recent outcomes.
    
    Returns:
    - active_provider: Currently configured triage provider
    - recent_outcomes: Last 20 triage operations with latency and fallback info
    """
    return ProvidersResponse(
        active_provider=settings.TRIAGE_PROVIDER,
        recent_outcomes=ComplaintService.get_recent_triage_outcomes(),
    )


@router.get("/health", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    """
    Liveness check.
    
    NEVER touches the database - a slow DB must not cause pod restarts.
    Always returns 200 if the service is running.
    """
    return HealthResponse(
        status="healthy",
        service="civicpulse-backend",
    )


@router.get(
    "/ready",
    response_model=ReadyResponse,
    responses={
        503: {"description": "Service not ready"},
    },
    tags=["health"],
)
def readiness_check(db: Session = Depends(get_db)) -> ReadyResponse:
    """
    Readiness check.
    
    Checks that both PostgreSQL and Redis are reachable.
    Returns 200 only if both dependencies are healthy.
    Returns 503 with details if either dependency is unavailable.
    """
    postgres_status = "unhealthy"
    redis_status = "unhealthy"
    
    # Check PostgreSQL
    try:
        db.execute(text("SELECT 1"))
        postgres_status = "healthy"
    except Exception:
        pass
    
    # Check Redis
    try:
        redis_service = RedisService()
        if redis_service.is_healthy():
            redis_status = "healthy"
    except Exception:
        pass
    
    # Return 503 if any dependency is unhealthy
    if postgres_status != "healthy" or redis_status != "healthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "postgres": postgres_status,
                "redis": redis_status,
            },
        )
    
    return ReadyResponse(
        status="ready",
        postgres=postgres_status,
        redis=redis_status,
    )
