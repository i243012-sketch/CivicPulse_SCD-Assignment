"""FastAPI application entry point."""
import signal
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint

from app.core.config import settings
from app.core.database import close_db_connections
from app.core.logging import get_logger, setup_logging
from app.core.metrics import request_count, request_latency
from app.routes import complaints, meta, metrics, stats

# Setup logging first
setup_logging()
logger = get_logger(__name__)

# Flag for graceful shutdown
shutdown_event = False


def handle_sigterm(signum: int, frame: object) -> None:
    """Handle SIGTERM signal for graceful shutdown."""
    global shutdown_event
    logger.info("Received SIGTERM, initiating graceful shutdown")
    shutdown_event = True


# Register SIGTERM handler
signal.signal(signal.SIGTERM, handle_sigterm)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        "Starting CivicPulse backend",
        extra={
            "extra_fields": {
                "triage_provider": settings.TRIAGE_PROVIDER,
                "debug": settings.DEBUG,
            }
        },
    )

    yield

    # Shutdown
    logger.info("Shutting down CivicPulse backend")
    close_db_connections()
    logger.info("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title="CivicPulse API",
    description="Municipal complaint intake and triage system",
    version="1.0.0",
    lifespan=lifespan,
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    """
    Middleware to add request ID to all requests.

    Takes X-Request-ID from header if present, otherwise generates one.
    Echoes the request ID back in the response headers.
    Attaches request_id to logs for tracing.
    """
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    # Store in request state for access in route handlers
    request.state.request_id = request_id

    # Process request
    response = await call_next(request)

    # Echo request ID in response
    response.headers["X-Request-ID"] = request_id

    return response


@app.middleware("http")
async def metrics_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    """
    Middleware to record request metrics.

    Records:
    - Request count by method/endpoint/status
    - Request latency by method/endpoint
    """
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate latency
    latency = time.time() - start_time

    # Extract endpoint (path template, not actual path with IDs)
    endpoint = request.url.path
    method = request.method
    status_code = response.status_code

    # Record metrics
    request_count.labels(
        method=method,
        endpoint=endpoint,
        status_code=status_code,
    ).inc()

    request_latency.labels(
        method=method,
        endpoint=endpoint,
    ).observe(latency)

    return response


@app.middleware("http")
async def shutdown_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    """
    Middleware to reject new requests during graceful shutdown.

    When shutdown_event is set, return 503 for new requests
    but allow in-flight requests to complete.
    """
    if shutdown_event:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Service is shutting down"},
        )

    return await call_next(request)


# Include routers
app.include_router(complaints.router)
app.include_router(stats.router)
app.include_router(meta.router)
app.include_router(metrics.router)

# Health endpoints at root level (duplicated for convenience)
app.include_router(meta.router, prefix="", tags=["health"])


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "service": "CivicPulse API",
        "version": "1.0.0",
        "status": "operational",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config=None,  # Use our custom logging
    )
