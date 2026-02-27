"""add expense_category and expense

Revision ID: 0005
Revises: 0004
Create Date: 2026-02-22

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "expense_categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_expense_categories_code"),
    )

    op.create_table(
        "expenses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("cooperative_id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column("document_number", sa.String(length=50), nullable=True),
        sa.Column("description", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="created"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["cooperative_id"], ["cooperatives.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["expense_categories.id"]),
        sa.CheckConstraint("amount > 0", name="ck_expenses_amount_positive"),
    )
    op.create_index(
        op.f("ix_expenses_cooperative_id"), "expenses", ["cooperative_id"], unique=False
    )
    op.create_index(op.f("ix_expenses_category_id"), "expenses", ["category_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_expenses_category_id"), table_name="expenses")
    op.drop_index(op.f("ix_expenses_cooperative_id"), table_name="expenses")
    op.drop_table("expenses")
    op.drop_table("expense_categories")
