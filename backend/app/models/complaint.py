"""Complaint SQLAlchemy model."""
import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Enum, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Category(str, enum.Enum):
    """Complaint category enumeration."""

    WATER = "water"
    ELECTRICITY = "electricity"
    SANITATION = "sanitation"
    ROADS = "roads"
    STREETLIGHTS = "streetlights"
    OTHER = "other"


class Priority(str, enum.Enum):
    """Complaint priority enumeration."""

    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class Status(str, enum.Enum):
    """Complaint status enumeration."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"


# State machine transition table
ALLOWED_TRANSITIONS: dict[Status, set[Status]] = {
    Status.OPEN: {Status.IN_PROGRESS, Status.REJECTED},
    Status.IN_PROGRESS: {Status.RESOLVED, Status.REJECTED},
    Status.RESOLVED: set(),  # Terminal state
    Status.REJECTED: set(),  # Terminal state
}


def is_valid_transition(from_status: Status, to_status: Status) -> bool:
    """Check if a status transition is valid according to the state machine."""
    return to_status in ALLOWED_TRANSITIONS.get(from_status, set())


class Complaint(Base):
    """Complaint model representing a municipal complaint."""

    __tablename__ = "complaints"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    # Core complaint data
    text: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    reporter_contact: Mapped[str | None] = mapped_column(String(200), nullable=True)
    
    # Triage results
    category: Mapped[Category] = mapped_column(
        Enum(Category, name="category_enum", native_enum=False),
        nullable=False,
    )
    priority: Mapped[Priority] = mapped_column(
        Enum(Priority, name="priority_enum", native_enum=False),
        nullable=False,
    )
    status: Mapped[Status] = mapped_column(
        Enum(Status, name="status_enum", native_enum=False),
        nullable=False,
        default=Status.OPEN,
    )
    
    # AI triage metadata
    ai_summary: Mapped[str | None] = mapped_column(String(140), nullable=True)
    triaged_by: Mapped[str] = mapped_column(String(50), nullable=False)
    triage_latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        """String representation of a Complaint."""
        return (
            f"<Complaint(id={self.id}, category={self.category.value}, "
            f"priority={self.priority.value}, status={self.status.value})>"
        )
