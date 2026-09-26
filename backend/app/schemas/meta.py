"""Pydantic schemas for meta/system endpoints."""
from pydantic import BaseModel

from app.schemas.triage import TriageOutcome


class ProvidersResponse(BaseModel):
    """Schema for providers metadata endpoint."""

    active_provider: str
    recent_outcomes: list[TriageOutcome]


class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str
    service: str


class ReadyResponse(BaseModel):
    """Schema for readiness check response."""

    status: str
    postgres: str
    redis: str
