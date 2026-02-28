from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Guid


class Payment(Base):
    """Платёж по финансовому субъекту.

    Представляет собой поступление денежных средств от владельца (Owner)
    в счёт погашения задолженности финансового субъекта.
    Статусы: confirmed (подтверждён) → cancelled (отменён).
    """

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        {"comment": "Платежи по финансовым субъектам (поступления от владельцев)"},
    )

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    financial_subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("financial_subjects.id"),
        nullable=False,
        index=True,
        comment="ID финансового субъекта",
    )
    payer_owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("owners.id"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    document_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="confirmed")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        comment="Дата и время последнего обновления записи",
    )

    financial_subject: Mapped["FinancialSubject"] = relationship(
        "FinancialSubject", back_populates="payments"
    )
    payer: Mapped["Owner"] = relationship("Owner", back_populates="payments")
