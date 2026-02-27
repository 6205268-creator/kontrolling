"""add contribution_type, accrual, payment

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-22

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "contribution_types",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_contribution_types_code"),
    )

    op.create_table(
        "accruals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("financial_subject_id", sa.Uuid(), nullable=False),
        sa.Column("contribution_type_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("accrual_date", sa.Date(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="created"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["financial_subject_id"], ["financial_subjects.id"]),
        sa.ForeignKeyConstraint(["contribution_type_id"], ["contribution_types.id"]),
        sa.CheckConstraint("amount >= 0", name="ck_accruals_amount_non_negative"),
    )
    op.create_index(
        op.f("ix_accruals_financial_subject_id"), "accruals", ["financial_subject_id"], unique=False
    )
    op.create_index(
        op.f("ix_accruals_contribution_type_id"), "accruals", ["contribution_type_id"], unique=False
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("financial_subject_id", sa.Uuid(), nullable=False),
        sa.Column("payer_owner_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("document_number", sa.String(length=50), nullable=True),
        sa.Column("description", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="confirmed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["financial_subject_id"], ["financial_subjects.id"]),
        sa.ForeignKeyConstraint(["payer_owner_id"], ["owners.id"]),
        sa.CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
    )
    op.create_index(
        op.f("ix_payments_financial_subject_id"), "payments", ["financial_subject_id"], unique=False
    )
    op.create_index(op.f("ix_payments_payer_owner_id"), "payments", ["payer_owner_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_payments_payer_owner_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_financial_subject_id"), table_name="payments")
    op.drop_table("payments")
    op.drop_index(op.f("ix_accruals_contribution_type_id"), table_name="accruals")
    op.drop_index(op.f("ix_accruals_financial_subject_id"), table_name="accruals")
    op.drop_table("accruals")
    op.drop_table("contribution_types")
