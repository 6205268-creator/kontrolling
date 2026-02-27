"""add history tables for audit (plot_ownerships, accruals, payments, expenses)

Revision ID: 0009
Revises: 0008
Create Date: 2026-02-24

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "plot_ownerships_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("operation", sa.String(length=10), nullable=False),
        sa.Column("land_plot_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("share_numerator", sa.Integer(), nullable=False),
        sa.Column("share_denominator", sa.Integer(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_plot_ownerships_history_entity_id"),
        "plot_ownerships_history",
        ["entity_id"],
        unique=False,
    )

    op.create_table(
        "accruals_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("operation", sa.String(length=10), nullable=False),
        sa.Column("financial_subject_id", sa.Uuid(), nullable=False),
        sa.Column("contribution_type_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("accrual_date", sa.Date(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_accruals_history_entity_id"),
        "accruals_history",
        ["entity_id"],
        unique=False,
    )

    op.create_table(
        "payments_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("operation", sa.String(length=10), nullable=False),
        sa.Column("financial_subject_id", sa.Uuid(), nullable=False),
        sa.Column("payer_owner_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("document_number", sa.String(length=50), nullable=True),
        sa.Column("description", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_payments_history_entity_id"),
        "payments_history",
        ["entity_id"],
        unique=False,
    )

    op.create_table(
        "expenses_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("operation", sa.String(length=10), nullable=False),
        sa.Column("cooperative_id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column("document_number", sa.String(length=50), nullable=True),
        sa.Column("description", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_expenses_history_entity_id"),
        "expenses_history",
        ["entity_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_expenses_history_entity_id"), table_name="expenses_history")
    op.drop_table("expenses_history")
    op.drop_index(op.f("ix_payments_history_entity_id"), table_name="payments_history")
    op.drop_table("payments_history")
    op.drop_index(op.f("ix_accruals_history_entity_id"), table_name="accruals_history")
    op.drop_table("accruals_history")
    op.drop_index(op.f("ix_plot_ownerships_history_entity_id"), table_name="plot_ownerships_history")
    op.drop_table("plot_ownerships_history")
