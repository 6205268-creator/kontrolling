"""add land_plot and plot_ownership

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-22

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "land_plots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("cooperative_id", sa.Uuid(), nullable=False),
        sa.Column("plot_number", sa.String(length=50), nullable=False),
        sa.Column("area_sqm", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("cadastral_number", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["cooperative_id"], ["cooperatives.id"]),
        sa.UniqueConstraint("cooperative_id", "plot_number", name="uq_land_plots_cooperative_plot_number"),
    )
    op.create_index(op.f("ix_land_plots_cooperative_id"), "land_plots", ["cooperative_id"], unique=False)
    op.create_index(op.f("ix_land_plots_plot_number"), "land_plots", ["plot_number"], unique=False)

    op.create_table(
        "plot_ownerships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("land_plot_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("share_numerator", sa.Integer(), nullable=False),
        sa.Column("share_denominator", sa.Integer(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["land_plot_id"], ["land_plots.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["owners.id"]),
        sa.CheckConstraint("share_numerator <= share_denominator", name="ck_plot_ownership_share"),
    )
    op.create_index(op.f("ix_plot_ownerships_land_plot_id"), "plot_ownerships", ["land_plot_id"], unique=False)
    op.create_index(op.f("ix_plot_ownerships_owner_id"), "plot_ownerships", ["owner_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_plot_ownerships_owner_id"), table_name="plot_ownerships")
    op.drop_index(op.f("ix_plot_ownerships_land_plot_id"), table_name="plot_ownerships")
    op.drop_table("plot_ownerships")
    op.drop_index(op.f("ix_land_plots_plot_number"), table_name="land_plots")
    op.drop_index(op.f("ix_land_plots_cooperative_id"), table_name="land_plots")
    op.drop_table("land_plots")
