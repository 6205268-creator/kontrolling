"""init v2 schema (physical_person, snt, snt_member, plot, plot_owner)

Revision ID: 0001_init_v2
Revises:
Create Date: 2026-01-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_init_v2"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "physical_person",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(250), nullable=False),
        sa.Column("inn", sa.String(12), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(datetime('now'))"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(datetime('now'))"), nullable=False),
    )

    op.create_table(
        "snt",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(datetime('now'))"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(datetime('now'))"), nullable=False),
    )

    op.create_table(
        "plot",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snt_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(datetime('now'))"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(datetime('now'))"), nullable=False),
        sa.ForeignKeyConstraint(["snt_id"], ["snt.id"], name="fk_plot_snt", ondelete="RESTRICT"),
        sa.UniqueConstraint("snt_id", "number", name="uq_plot_snt_number"),
    )

    op.create_table(
        "snt_member",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snt_id", sa.Integer(), nullable=False),
        sa.Column("physical_person_id", sa.Integer(), nullable=False),
        sa.Column("date_from", sa.Date(), nullable=False),
        sa.Column("date_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(datetime('now'))"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(datetime('now'))"), nullable=False),
        sa.ForeignKeyConstraint(["snt_id"], ["snt.id"], name="fk_snt_member_snt", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["physical_person_id"], ["physical_person.id"], name="fk_snt_member_person", ondelete="RESTRICT"),
        sa.UniqueConstraint("snt_id", "physical_person_id", "date_from", name="uq_snt_member_snt_person_from"),
    )

    op.create_table(
        "plot_owner",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snt_id", sa.Integer(), nullable=False),
        sa.Column("plot_id", sa.Integer(), nullable=False),
        sa.Column("physical_person_id", sa.Integer(), nullable=False),
        sa.Column("date_from", sa.Date(), nullable=False),
        sa.Column("date_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(datetime('now'))"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(datetime('now'))"), nullable=False),
        sa.ForeignKeyConstraint(["snt_id"], ["snt.id"], name="fk_plot_owner_snt", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["plot_id"], ["plot.id"], name="fk_plot_owner_plot", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["physical_person_id"], ["physical_person.id"], name="fk_plot_owner_person", ondelete="RESTRICT"),
        sa.UniqueConstraint("snt_id", "plot_id", "physical_person_id", "date_from", name="uq_plot_owner_snt_plot_person_from"),
    )

    op.create_index("ix_plot_snt_id", "plot", ["snt_id"])
    op.create_index("ix_snt_member_snt_id", "snt_member", ["snt_id"])
    op.create_index("ix_snt_member_physical_person_id", "snt_member", ["physical_person_id"])
    op.create_index("ix_plot_owner_snt_id", "plot_owner", ["snt_id"])
    op.create_index("ix_plot_owner_physical_person_id", "plot_owner", ["physical_person_id"])


def downgrade() -> None:
    op.drop_index("ix_plot_owner_physical_person_id", table_name="plot_owner")
    op.drop_index("ix_plot_owner_snt_id", table_name="plot_owner")
    op.drop_index("ix_snt_member_physical_person_id", table_name="snt_member")
    op.drop_index("ix_snt_member_snt_id", table_name="snt_member")
    op.drop_index("ix_plot_snt_id", table_name="plot")
    op.drop_table("plot_owner")
    op.drop_table("snt_member")
    op.drop_table("plot")
    op.drop_table("snt")
    op.drop_table("physical_person")
