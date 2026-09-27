"""Pydantic schemas for error responses."""
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Detail of a validation error."""

    field: str
    message: str


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    detail: str | list[ErrorDetail]


class StateTransitionError(BaseModel):
    """Schema for state transition errors."""

    detail: str
    from_status: str
    to_status: str
