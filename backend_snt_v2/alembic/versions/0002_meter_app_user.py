"""add meter, app_user

Revision ID: 0002_meter_app_user
Revises: 0001_init_v2
Create Date: 2026-01-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_meter_app_user"
down_revision: Union[str, Sequence[str], None] = "0001_init_v2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("snt_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(datetime('now'))"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(datetime('now'))"), nullable=False),
        sa.ForeignKeyConstraint(["snt_id"], ["snt.id"], name="fk_app_user_snt", ondelete="RESTRICT"),
    )
    op.create_index("ix_app_user_snt_id", "app_user", ["snt_id"])

    op.create_table(
        "meter",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snt_id", sa.Integer(), nullable=False),
        sa.Column("plot_id", sa.Integer(), nullable=False),
        sa.Column("meter_type", sa.String(50), nullable=False),
        sa.Column("serial_number", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(datetime('now'))"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(datetime('now'))"), nullable=False),
        sa.ForeignKeyConstraint(["snt_id"], ["snt.id"], name="fk_meter_snt", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["plot_id"], ["plot.id"], name="fk_meter_plot", ondelete="RESTRICT"),
        sa.UniqueConstraint("snt_id", "plot_id", "meter_type", name="uq_meter_snt_plot_type"),
    )
    op.create_index("ix_meter_snt_id", "meter", ["snt_id"])
    op.create_index("ix_meter_plot_id", "meter", ["plot_id"])


def downgrade() -> None:
    op.drop_index("ix_meter_plot_id", table_name="meter")
    op.drop_index("ix_meter_snt_id", table_name="meter")
    op.drop_table("meter")
    op.drop_index("ix_app_user_snt_id", table_name="app_user")
    op.drop_table("app_user")
