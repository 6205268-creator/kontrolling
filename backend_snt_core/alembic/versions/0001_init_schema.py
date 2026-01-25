"""init schema

Revision ID: 0001_init_schema
Revises: 
Create Date: 2026-01-20

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_init_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "snt",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "plot",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snt_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["snt_id"], ["snt.id"], name="fk_plot_snt", ondelete="RESTRICT"),
        sa.UniqueConstraint("snt_id", "number", name="uq_plot_snt_number"),
        sa.UniqueConstraint("snt_id", "id", name="uq_plot_snt_id"),
    )

    op.create_table(
        "owner",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snt_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=250), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["snt_id"], ["snt.id"], name="fk_owner_snt", ondelete="RESTRICT"),
        sa.UniqueConstraint("snt_id", "full_name", name="uq_owner_snt_full_name"),
        sa.UniqueConstraint("snt_id", "id", name="uq_owner_snt_id"),
    )

    op.create_table(
        "plot_owner",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snt_id", sa.Integer(), nullable=False),
        sa.Column("plot_id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("date_from", sa.Date(), nullable=False),
        sa.Column("date_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["snt_id"], ["snt.id"], name="fk_plot_owner_snt", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["snt_id", "plot_id"], ["plot.snt_id", "plot.id"], name="fk_plot_owner_plot", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["snt_id", "owner_id"], ["owner.snt_id", "owner.id"], name="fk_plot_owner_owner", ondelete="RESTRICT"),
        sa.UniqueConstraint("snt_id", "plot_id", "owner_id", "date_from", name="uq_plot_owner_period"),
    )

    op.create_table(
        "charge_item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snt_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=250), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["snt_id"], ["snt.id"], name="fk_charge_item_snt", ondelete="RESTRICT"),
        sa.UniqueConstraint("snt_id", "name", name="uq_charge_item_snt_name"),
        sa.UniqueConstraint("snt_id", "id", name="uq_charge_item_snt_id"),
    )

    op.create_table(
        "doc_accrual",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snt_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.String(length=50), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("is_posted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["snt_id"], ["snt.id"], name="fk_doc_accrual_snt", ondelete="RESTRICT"),
        sa.UniqueConstraint("snt_id", "number", name="uq_doc_accrual_snt_number"),
        sa.UniqueConstraint("snt_id", "id", name="uq_doc_accrual_snt_id"),
    )

    op.create_table(
        "doc_accrual_row",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snt_id", sa.Integer(), nullable=False),
        sa.Column("doc_id", sa.Integer(), nullable=False),
        sa.Column("plot_id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("charge_item_id", sa.Integer(), nullable=False),
        sa.Column("period_from", sa.Date(), nullable=True),
        sa.Column("period_to", sa.Date(), nullable=True),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["snt_id", "doc_id"], ["doc_accrual.snt_id", "doc_accrual.id"], name="fk_doc_accrual_row_doc", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["snt_id", "plot_id"], ["plot.snt_id", "plot.id"], name="fk_doc_accrual_row_plot", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["snt_id", "owner_id"], ["owner.snt_id", "owner.id"], name="fk_doc_accrual_row_owner", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["snt_id", "charge_item_id"], ["charge_item.snt_id", "charge_item.id"], name="fk_doc_accrual_row_charge_item", ondelete="RESTRICT"),
        sa.CheckConstraint("amount > 0", name="chk_doc_accrual_row_amount_positive"),
        sa.UniqueConstraint("snt_id", "id", "doc_id", name="uq_doc_accrual_row_id_doc"),
    )

    op.create_table(
        "doc_payment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snt_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.String(length=50), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("is_posted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["snt_id"], ["snt.id"], name="fk_doc_payment_snt", ondelete="RESTRICT"),
        sa.UniqueConstraint("snt_id", "number", name="uq_doc_payment_snt_number"),
        sa.UniqueConstraint("snt_id", "id", name="uq_doc_payment_snt_id"),
    )

    op.create_table(
        "doc_payment_row",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snt_id", sa.Integer(), nullable=False),
        sa.Column("doc_id", sa.Integer(), nullable=False),
        sa.Column("plot_id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("charge_item_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["snt_id", "doc_id"], ["doc_payment.snt_id", "doc_payment.id"], name="fk_doc_payment_row_doc", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["snt_id", "plot_id"], ["plot.snt_id", "plot.id"], name="fk_doc_payment_row_plot", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["snt_id", "owner_id"], ["owner.snt_id", "owner.id"], name="fk_doc_payment_row_owner", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["snt_id", "charge_item_id"], ["charge_item.snt_id", "charge_item.id"], name="fk_doc_payment_row_charge_item", ondelete="RESTRICT"),
        sa.CheckConstraint("amount > 0", name="chk_doc_payment_row_amount_positive"),
        sa.UniqueConstraint("snt_id", "id", "doc_id", name="uq_doc_payment_row_id_doc"),
    )

    op.create_table(
        "reg_balance",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snt_id", sa.Integer(), nullable=False),
        sa.Column("doc_accrual_id", sa.Integer(), nullable=True),
        sa.Column("doc_accrual_row_id", sa.Integer(), nullable=True),
        sa.Column("doc_payment_id", sa.Integer(), nullable=True),
        sa.Column("doc_payment_row_id", sa.Integer(), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("plot_id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("charge_item_id", sa.Integer(), nullable=False),
        sa.Column("amount_debit", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("amount_credit", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["snt_id"], ["snt.id"], name="fk_reg_balance_snt", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["snt_id", "doc_accrual_id"], ["doc_accrual.snt_id", "doc_accrual.id"], name="fk_reg_balance_doc_accrual", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["snt_id", "doc_accrual_row_id", "doc_accrual_id"], ["doc_accrual_row.snt_id", "doc_accrual_row.id", "doc_accrual_row.doc_id"], name="fk_reg_balance_doc_accrual_row", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["snt_id", "doc_payment_id"], ["doc_payment.snt_id", "doc_payment.id"], name="fk_reg_balance_doc_payment", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["snt_id", "doc_payment_row_id", "doc_payment_id"], ["doc_payment_row.snt_id", "doc_payment_row.id", "doc_payment_row.doc_id"], name="fk_reg_balance_doc_payment_row", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["snt_id", "plot_id"], ["plot.snt_id", "plot.id"], name="fk_reg_balance_plot", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["snt_id", "owner_id"], ["owner.snt_id", "owner.id"], name="fk_reg_balance_owner", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["snt_id", "charge_item_id"], ["charge_item.snt_id", "charge_item.id"], name="fk_reg_balance_charge_item", ondelete="RESTRICT"),
        sa.CheckConstraint(
            "("
            " (doc_accrual_id IS NOT NULL AND doc_accrual_row_id IS NOT NULL"
            "   AND doc_payment_id IS NULL AND doc_payment_row_id IS NULL)"
            " OR "
            " (doc_payment_id IS NOT NULL AND doc_payment_row_id IS NOT NULL"
            "   AND doc_accrual_id IS NULL AND doc_accrual_row_id IS NULL)"
            ")",
            name="chk_reg_balance_exactly_one_doc_type",
        ),
        sa.CheckConstraint("(amount_debit >= 0 AND amount_credit >= 0)", name="chk_reg_balance_amounts_non_negative"),
        sa.CheckConstraint("NOT (amount_debit > 0 AND amount_credit > 0)", name="chk_reg_balance_not_both_sides"),
    )

    op.create_index("ix_plot_snt_id", "plot", ["snt_id"])
    op.create_index("ix_owner_snt_id", "owner", ["snt_id"])
    op.create_index("ix_charge_item_snt_id", "charge_item", ["snt_id"])
    op.create_index("ix_doc_accrual_snt_id", "doc_accrual", ["snt_id"])
    op.create_index("ix_doc_payment_snt_id", "doc_payment", ["snt_id"])
    op.create_index("ix_reg_balance_snt_id", "reg_balance", ["snt_id"])


def downgrade() -> None:
    op.drop_index("ix_reg_balance_snt_id", table_name="reg_balance")
    op.drop_index("ix_doc_payment_snt_id", table_name="doc_payment")
    op.drop_index("ix_doc_accrual_snt_id", table_name="doc_accrual")
    op.drop_index("ix_charge_item_snt_id", table_name="charge_item")
    op.drop_index("ix_owner_snt_id", table_name="owner")
    op.drop_index("ix_plot_snt_id", table_name="plot")

    op.drop_table("reg_balance")
    op.drop_table("doc_payment_row")
    op.drop_table("doc_payment")
    op.drop_table("doc_accrual_row")
    op.drop_table("doc_accrual")
    op.drop_table("charge_item")
    op.drop_table("plot_owner")
    op.drop_table("owner")
    op.drop_table("plot")
    op.drop_table("snt")

