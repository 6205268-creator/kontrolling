"""add due_date to accruals and accruals_history

Revision ID: 0012
Revises: 0011
Create Date: 2026-03-20

Phase 1.1: Add due_date column for payment deadline tracking.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add due_date to accruals table
    op.add_column(
        "accruals",
        sa.Column("due_date", sa.Date(), nullable=True),
    )
    
    # Add due_date to accruals_history table
    op.add_column(
        "accruals_history",
        sa.Column("due_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    # Remove due_date from accruals_history table
    op.drop_column("accruals_history", "due_date")
    
    # Remove due_date from accruals table
    op.drop_column("accruals", "due_date")
