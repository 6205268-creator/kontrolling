from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RegBalance(Base):
    __tablename__ = "reg_balance"
    __table_args__ = (
        ForeignKeyConstraint(
            ["snt_id"],
            ["snt.id"],
            name="fk_reg_balance_snt",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["snt_id", "doc_accrual_id"],
            ["doc_accrual.snt_id", "doc_accrual.id"],
            name="fk_reg_balance_doc_accrual",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["snt_id", "doc_accrual_row_id", "doc_accrual_id"],
            ["doc_accrual_row.snt_id", "doc_accrual_row.id", "doc_accrual_row.doc_id"],
            name="fk_reg_balance_doc_accrual_row",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["snt_id", "doc_payment_id"],
            ["doc_payment.snt_id", "doc_payment.id"],
            name="fk_reg_balance_doc_payment",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["snt_id", "doc_payment_row_id", "doc_payment_id"],
            ["doc_payment_row.snt_id", "doc_payment_row.id", "doc_payment_row.doc_id"],
            name="fk_reg_balance_doc_payment_row",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["snt_id", "plot_id"],
            ["plot.snt_id", "plot.id"],
            name="fk_reg_balance_plot",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["snt_id", "owner_id"],
            ["owner.snt_id", "owner.id"],
            name="fk_reg_balance_owner",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["snt_id", "charge_item_id"],
            ["charge_item.snt_id", "charge_item.id"],
            name="fk_reg_balance_charge_item",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "("
            " (doc_accrual_id IS NOT NULL AND doc_accrual_row_id IS NOT NULL"
            "   AND doc_payment_id IS NULL AND doc_payment_row_id IS NULL)"
            " OR "
            " (doc_payment_id IS NOT NULL AND doc_payment_row_id IS NOT NULL"
            "   AND doc_accrual_id IS NULL AND doc_accrual_row_id IS NULL)"
            ")",
            name="chk_reg_balance_exactly_one_doc_type",
        ),
        CheckConstraint(
            "(amount_debit >= 0 AND amount_credit >= 0)",
            name="chk_reg_balance_amounts_non_negative",
        ),
        CheckConstraint(
            "NOT (amount_debit > 0 AND amount_credit > 0)",
            name="chk_reg_balance_not_both_sides",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snt_id: Mapped[int] = mapped_column(Integer, nullable=False)

    doc_accrual_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    doc_accrual_row_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    doc_payment_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    doc_payment_row_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    date: Mapped[date] = mapped_column(Date, nullable=False)

    plot_id: Mapped[int] = mapped_column(Integer, nullable=False)
    owner_id: Mapped[int] = mapped_column(Integer, nullable=False)
    charge_item_id: Mapped[int] = mapped_column(Integer, nullable=False)

    amount_debit: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, server_default="0")
    amount_credit: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, server_default="0")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

