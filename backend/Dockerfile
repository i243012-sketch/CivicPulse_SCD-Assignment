# Multi-stage build for CivicPulse Backend
# Stage 1: Builder
FROM python:3.12-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY backend/pyproject.toml ./

# Install dependencies to a local directory
RUN pip install --no-cache-dir --user \
    fastapi==0.109.0 \
    uvicorn[standard]==0.27.0 \
    pydantic==2.5.3 \
    pydantic-settings==2.1.0 \
    sqlalchemy==2.0.25 \
    alembic==1.13.1 \
    psycopg2-binary==2.9.9 \
    redis==5.0.1 \
    httpx==0.26.0 \
    groq==0.4.1 \
    prometheus-client==0.19.0 \
    python-multipart==0.0.6

# Stage 2: Runtime
FROM python:3.12-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser backend/app/ ./app/
COPY --chown=appuser:appuser backend/alembic/ ./alembic/
COPY --chown=appuser:appuser backend/alembic.ini ./
COPY --chown=appuser:appuser scripts/ ./scripts/

# Ensure the non-root user can access the PATH
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
