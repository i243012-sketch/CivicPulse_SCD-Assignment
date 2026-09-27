"""Repository for complaint database operations - ALL SQL lives here."""
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.complaint import Category, Complaint, Priority, Status


class ComplaintRepository:
    """Repository handling all database operations for complaints."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def create(self, complaint: Complaint) -> Complaint:
        """
        Create a new complaint in the database.

        Args:
            complaint: Complaint model instance to persist

        Returns:
            The persisted complaint with database-generated fields
        """
        self.db.add(complaint)
        self.db.commit()
        self.db.refresh(complaint)
        return complaint

    def get_by_id(self, complaint_id: UUID) -> Complaint | None:
        """
        Get a complaint by ID.

        Args:
            complaint_id: UUID of the complaint

        Returns:
            Complaint if found, None otherwise
        """
        stmt = select(Complaint).where(Complaint.id == complaint_id)
        return self.db.scalar(stmt)

    def get_all(
        self,
        category: Category | None = None,
        priority: Priority | None = None,
        status: Status | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Complaint], int]:
        """
        Get all complaints with optional filtering and pagination.

        Args:
            category: Filter by category (optional)
            priority: Filter by priority (optional)
            status: Filter by status (optional)
            page: Page number (1-indexed)
            page_size: Number of items per page (max 100)

        Returns:
            Tuple of (list of complaints, total count)
        """
        # Enforce max page size
        page_size = min(page_size, 100)

        # Build query with filters
        stmt = select(Complaint)

        if category is not None:
            stmt = stmt.where(Complaint.category == category)
        if priority is not None:
            stmt = stmt.where(Complaint.priority == priority)
        if status is not None:
            stmt = stmt.where(Complaint.status == status)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        # Apply pagination and ordering
        stmt = stmt.order_by(Complaint.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = self.db.scalars(stmt).all()

        return result, total

    def update_status(self, complaint: Complaint, new_status: Status) -> Complaint:
        """
        Update complaint status.

        Args:
            complaint: Complaint to update
            new_status: New status value

        Returns:
            Updated complaint
        """
        complaint.status = new_status
        self.db.commit()
        self.db.refresh(complaint)
        return complaint

    def get_stats_by_category(self) -> list[tuple[Category, int]]:
        """
        Get complaint counts grouped by category.

        Returns:
            List of (category, count) tuples
        """
        stmt = (
            select(Complaint.category, func.count(Complaint.id))
            .group_by(Complaint.category)
            .order_by(Complaint.category)
        )
        result = self.db.execute(stmt).all()
        return [(row[0], row[1]) for row in result]

    def get_stats_by_priority(self) -> list[tuple[Priority, int]]:
        """
        Get complaint counts grouped by priority.

        Returns:
            List of (priority, count) tuples
        """
        stmt = (
            select(Complaint.priority, func.count(Complaint.id))
            .group_by(Complaint.priority)
            .order_by(Complaint.priority)
        )
        result = self.db.execute(stmt).all()
        return [(row[0], row[1]) for row in result]

    def get_total_count(self) -> int:
        """
        Get total count of all complaints.

        Returns:
            Total number of complaints
        """
        stmt = select(func.count(Complaint.id))
        return self.db.scalar(stmt) or 0
