"""Routes for Prometheus metrics endpoint."""
from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
def metrics() -> Response:
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format:
    - http_requests_total: Request count by method/endpoint/status
    - http_request_duration_seconds: Request latency histogram
    - triage_duration_milliseconds: Triage latency by provider
    - triage_fallback_total: Fallback counter by provider/reason
    - triage_cache_hits_total / triage_cache_misses_total
    - stats_cache_hits_total / stats_cache_misses_total
    - rate_limit_exceeded_total: Rate limit violations by IP
    """
    metrics_output = generate_latest()
    return Response(
        content=metrics_output,
        media_type=CONTENT_TYPE_LATEST,
    )
