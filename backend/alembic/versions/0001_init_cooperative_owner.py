"""init cooperative and owner

Revision ID: 0001
Revises:
Create Date: 2026-02-22

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cooperatives",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("unp", sa.String(length=20), nullable=True),
        sa.Column("address", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cooperatives_name"), "cooperatives", ["name"], unique=False)
    op.create_index(op.f("ix_cooperatives_unp"), "cooperatives", ["unp"], unique=True)

    op.create_table(
        "owners",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_type", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("tax_id", sa.String(length=20), nullable=True),
        sa.Column("contact_phone", sa.String(length=50), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_owners_tax_id"), "owners", ["tax_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_owners_tax_id"), table_name="owners")
    op.drop_table("owners")
    op.drop_index(op.f("ix_cooperatives_unp"), table_name="cooperatives")
    op.drop_index(op.f("ix_cooperatives_name"), table_name="cooperatives")
    op.drop_table("cooperatives")
