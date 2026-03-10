"""add financial operation audit fields (cancelled_at, operation_number, etc.)

Revision ID: 0011
Revises: 0010
Create Date: 2026-03-09

Ledger-ready MVP: audit fields for accruals, payments, expenses and their history tables.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ----- accruals -----
    op.add_column(
        "accruals",
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "accruals",
        sa.Column(
            "cancelled_by_user_id",
            sa.Uuid(),
            sa.ForeignKey("app_users.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "accruals",
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "accruals",
        sa.Column("operation_number", sa.String(length=50), nullable=True),
    )
    # Backfill operation_number for existing rows
    op.execute(
        "UPDATE accruals SET operation_number = 'ACC-' || id::text WHERE operation_number IS NULL"
    )
    op.alter_column(
        "accruals",
        "operation_number",
        existing_type=sa.String(50),
        nullable=False,
    )
    op.create_unique_constraint(
        "uq_accruals_operation_number", "accruals", ["operation_number"]
    )

    # ----- payments -----
    op.add_column(
        "payments",
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column(
            "cancelled_by_user_id",
            sa.Uuid(),
            sa.ForeignKey("app_users.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "payments",
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column("operation_number", sa.String(length=50), nullable=True),
    )
    op.execute(
        "UPDATE payments SET operation_number = 'PAY-' || id::text WHERE operation_number IS NULL"
    )
    op.alter_column(
        "payments",
        "operation_number",
        existing_type=sa.String(50),
        nullable=False,
    )
    op.create_unique_constraint(
        "uq_payments_operation_number", "payments", ["operation_number"]
    )

    # ----- expenses -----
    op.add_column(
        "expenses",
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "expenses",
        sa.Column(
            "cancelled_by_user_id",
            sa.Uuid(),
            sa.ForeignKey("app_users.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "expenses",
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "expenses",
        sa.Column("operation_number", sa.String(length=50), nullable=True),
    )
    op.execute(
        "UPDATE expenses SET operation_number = 'EXP-' || id::text WHERE operation_number IS NULL"
    )
    op.alter_column(
        "expenses",
        "operation_number",
        existing_type=sa.String(50),
        nullable=False,
    )
    op.create_unique_constraint(
        "uq_expenses_operation_number", "expenses", ["operation_number"]
    )

    # ----- history tables (nullable, no backfill) -----
    for table in ("accruals_history", "payments_history", "expenses_history"):
        op.add_column(
            table,
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.add_column(
            table,
            sa.Column("cancelled_by_user_id", sa.Uuid(), nullable=True),
        )
        op.add_column(
            table,
            sa.Column("cancellation_reason", sa.Text(), nullable=True),
        )
        op.add_column(
            table,
            sa.Column("operation_number", sa.String(length=50), nullable=True),
        )


def downgrade() -> None:
    for table in ("accruals_history", "payments_history", "expenses_history"):
        op.drop_column(table, "operation_number")
        op.drop_column(table, "cancellation_reason")
        op.drop_column(table, "cancelled_by_user_id")
        op.drop_column(table, "cancelled_at")

    op.drop_constraint("uq_expenses_operation_number", "expenses", type_="unique")
    op.drop_column("expenses", "operation_number")
    op.drop_column("expenses", "cancellation_reason")
    op.drop_column("expenses", "cancelled_by_user_id")
    op.drop_column("expenses", "cancelled_at")

    op.drop_constraint("uq_payments_operation_number", "payments", type_="unique")
    op.drop_column("payments", "operation_number")
    op.drop_column("payments", "cancellation_reason")
    op.drop_column("payments", "cancelled_by_user_id")
    op.drop_column("payments", "cancelled_at")

    op.drop_constraint("uq_accruals_operation_number", "accruals", type_="unique")
    op.drop_column("accruals", "operation_number")
    op.drop_column("accruals", "cancellation_reason")
    op.drop_column("accruals", "cancelled_by_user_id")
    op.drop_column("accruals", "cancelled_at")
