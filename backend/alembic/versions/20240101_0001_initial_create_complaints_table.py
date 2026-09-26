"""Initial migration: create complaints table

Revision ID: 20240101_0001
Revises: 
Create Date: 2024-01-01 00:01:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20240101_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create complaints table with all required fields and indexes."""
    # Create complaints table
    op.create_table(
        "complaints",
        # Primary key
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Core complaint data
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=False),
        sa.Column("reporter_contact", sa.String(length=200), nullable=True),
        # CHECK constraints for data validation
        sa.CheckConstraint("length(text) >= 10 AND length(text) <= 2000", name="check_text_length"),
        sa.CheckConstraint("length(location) >= 3 AND length(location) <= 200", name="check_location_length"),
        # Triage results
        sa.Column(
            "category",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "priority",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="open",
        ),
        # AI triage metadata
        sa.Column("ai_summary", sa.String(length=140), nullable=True),
        sa.Column("triaged_by", sa.String(length=50), nullable=False),
        sa.Column("triage_latency_ms", sa.Integer(), nullable=False),
        # Timestamps
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Create indexes for filtering and performance
    op.create_index(
        "ix_complaints_category",
        "complaints",
        ["category"],
    )
    op.create_index(
        "ix_complaints_priority",
        "complaints",
        ["priority"],
    )
    op.create_index(
        "ix_complaints_status",
        "complaints",
        ["status"],
    )
    op.create_index(
        "ix_complaints_created_at",
        "complaints",
        ["created_at"],
    )
    # Composite index for common query patterns (status + priority filtering)
    op.create_index(
        "ix_complaints_status_priority",
        "complaints",
        ["status", "priority"],
    )


def downgrade() -> None:
    """Drop complaints table and all indexes."""
    op.drop_index("ix_complaints_status_priority", table_name="complaints")
    op.drop_index("ix_complaints_created_at", table_name="complaints")
    op.drop_index("ix_complaints_status", table_name="complaints")
    op.drop_index("ix_complaints_priority", table_name="complaints")
    op.drop_index("ix_complaints_category", table_name="complaints")
    op.drop_table("complaints")
