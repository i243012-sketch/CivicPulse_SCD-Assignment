"""Pydantic schemas for triage results."""
from pydantic import BaseModel, Field

from app.models.complaint import Category, Priority


class TriageResult(BaseModel):
    """Result from a triage provider."""

    category: Category
    priority: Priority
    summary: str = Field(..., max_length=140)
    confidence: float = Field(..., ge=0.0, le=1.0)

    @property
    def is_high_confidence(self) -> bool:
        """Check if the triage has high confidence (>=0.7)."""
        return self.confidence >= 0.7


class TriageOutcome(BaseModel):
    """Record of a triage operation outcome for metadata tracking."""

    provider: str
    latency_ms: int
    fallback: bool
    timestamp: str
