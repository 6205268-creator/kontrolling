"""add app_user

Revision ID: 0007
Revises: 0006
Create Date: 2026-02-22

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "app_users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="treasurer"),
        sa.Column("cooperative_id", sa.Uuid(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["cooperative_id"], ["cooperatives.id"]),
    )
    op.create_index(op.f("ix_app_users_username"), "app_users", ["username"], unique=True)
    op.create_index(op.f("ix_app_users_email"), "app_users", ["email"], unique=True)
    op.create_index(op.f("ix_app_users_cooperative_id"), "app_users", ["cooperative_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_app_users_cooperative_id"), table_name="app_users")
    op.drop_index(op.f("ix_app_users_email"), table_name="app_users")
    op.drop_index(op.f("ix_app_users_username"), table_name="app_users")
    op.drop_table("app_users")
