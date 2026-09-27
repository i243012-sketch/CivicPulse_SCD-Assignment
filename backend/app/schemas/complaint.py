"""Pydantic schemas for complaint request/response validation."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.complaint import Category, Priority, Status


class ComplaintCreate(BaseModel):
    """Schema for creating a new complaint."""

    text: str = Field(..., min_length=10, max_length=2000)
    location: str = Field(..., min_length=3, max_length=200)
    reporter_contact: str | None = Field(None, max_length=200)

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate text field."""
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Text must be at least 10 characters after stripping whitespace")
        return v

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: str) -> str:
        """Validate location field."""
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Location must be at least 3 characters after stripping whitespace")
        return v


class ComplaintResponse(BaseModel):
    """Schema for complaint response."""

    id: UUID
    text: str
    location: str
    reporter_contact: str | None
    category: Category
    priority: Priority
    status: Status
    ai_summary: str | None
    triaged_by: str
    triage_latency_ms: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ComplaintListResponse(BaseModel):
    """Schema for paginated complaint list response."""

    items: list[ComplaintResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ComplaintStatusUpdate(BaseModel):
    """Schema for updating complaint status."""

    status: Status


class CategoryStats(BaseModel):
    """Statistics for a specific category."""

    category: Category
    count: int


class PriorityStats(BaseModel):
    """Statistics for a specific priority."""

    priority: Priority
    count: int


class StatsResponse(BaseModel):
    """Schema for statistics response."""

    by_category: list[CategoryStats]
    by_priority: list[PriorityStats]
    total_complaints: int
