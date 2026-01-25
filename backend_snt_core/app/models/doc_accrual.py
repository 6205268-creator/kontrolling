from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DocAccrual(Base):
    __tablename__ = "doc_accrual"
    __table_args__ = (
        UniqueConstraint("snt_id", "number", name="uq_doc_accrual_snt_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snt_id: Mapped[int] = mapped_column(ForeignKey("snt.id", ondelete="RESTRICT"), nullable=False)

    number: Mapped[str] = mapped_column(String(50), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    is_posted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class DocAccrualRow(Base):
    __tablename__ = "doc_accrual_row"
    __table_args__ = (
        UniqueConstraint("snt_id", "id", "doc_id", name="uq_doc_accrual_row_id_doc"),
        ForeignKeyConstraint(
            ["snt_id", "doc_id"],
            ["doc_accrual.snt_id", "doc_accrual.id"],
            name="fk_doc_accrual_row_doc",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["snt_id", "plot_id"],
            ["plot.snt_id", "plot.id"],
            name="fk_doc_accrual_row_plot",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["snt_id", "owner_id"],
            ["owner.snt_id", "owner.id"],
            name="fk_doc_accrual_row_owner",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["snt_id", "charge_item_id"],
            ["charge_item.snt_id", "charge_item.id"],
            name="fk_doc_accrual_row_charge_item",
            ondelete="RESTRICT",
        ),
        CheckConstraint("amount > 0", name="chk_doc_accrual_row_amount_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snt_id: Mapped[int] = mapped_column(Integer, nullable=False)

    doc_id: Mapped[int] = mapped_column(Integer, nullable=False)
    plot_id: Mapped[int] = mapped_column(Integer, nullable=False)
    owner_id: Mapped[int] = mapped_column(Integer, nullable=False)
    charge_item_id: Mapped[int] = mapped_column(Integer, nullable=False)

    period_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

