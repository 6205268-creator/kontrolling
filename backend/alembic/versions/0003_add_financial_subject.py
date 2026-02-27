"""add financial_subject

Revision ID: 0003
Revises: 0002
Create Date: 2026-02-22

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "financial_subjects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("subject_type", sa.String(length=30), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("cooperative_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["cooperative_id"], ["cooperatives.id"]),
        sa.UniqueConstraint("subject_type", "subject_id", "cooperative_id", name="uq_financial_subjects_type_subject_coop"),
        sa.UniqueConstraint("code", name="uq_financial_subjects_code"),
    )
    op.create_index(op.f("ix_financial_subjects_cooperative_id"), "financial_subjects", ["cooperative_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_financial_subjects_cooperative_id"), table_name="financial_subjects")
    op.drop_table("financial_subjects")
