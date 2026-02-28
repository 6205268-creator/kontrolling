from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Guid


class Accrual(Base):
    """Начисление по финансовому субъекту.

    Представляет собой задолженность по взносу или услуге за определённый период.
    Все начисления привязываются к FinancialSubject, а не напрямую к участку.
    Статусы: created (создано) → applied (применено) → cancelled (отменено).
    """

    __tablename__ = "accruals"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_accruals_amount_non_negative"),
        {"comment": "Начисления по финансовым субъектам (взносы, услуги)"},
    )

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    financial_subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("financial_subjects.id"),
        nullable=False,
        index=True,
        comment="ID финансового субъекта",
    )
    contribution_type_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contribution_types.id"),
        nullable=False,
        index=True,
        comment="ID вида взноса (членский, целевой и т.д.)",
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    accrual_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="created")
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
        "FinancialSubject", back_populates="accruals"
    )
    contribution_type: Mapped["ContributionType"] = relationship(
        "ContributionType", back_populates="accruals"
    )
