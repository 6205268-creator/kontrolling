"""add meter and meter_reading

Revision ID: 0006
Revises: 0005
Create Date: 2026-02-22

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "meters",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("meter_type", sa.String(length=20), nullable=False),
        sa.Column("serial_number", sa.String(length=100), nullable=True),
        sa.Column("installation_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["owner_id"], ["owners.id"]),
    )
    op.create_index(op.f("ix_meters_owner_id"), "meters", ["owner_id"], unique=False)

    op.create_table(
        "meter_readings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("meter_id", sa.Uuid(), nullable=False),
        sa.Column("reading_value", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("reading_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["meter_id"], ["meters.id"]),
        sa.UniqueConstraint("meter_id", "reading_date", name="uq_meter_readings_meter_date"),
    )
    op.create_index(
        op.f("ix_meter_readings_meter_id"), "meter_readings", ["meter_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_meter_readings_meter_id"), table_name="meter_readings")
    op.drop_table("meter_readings")
    op.drop_index(op.f("ix_meters_owner_id"), table_name="meters")
    op.drop_table("meters")
