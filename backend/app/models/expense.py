from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Guid


class Expense(Base):
    """Расход садоводческого товарищества.

    Отдельный финансовый поток — расходы СТ как юридического лица.
    Не привязан к FinancialSubject (в отличие от начислений и платежей).
    Примеры: ремонт дорог, зарплата председателя, закупка материалов.
    Статусы: created (создан) → confirmed (подтверждён) → cancelled (отменён).
    """

    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_expenses_amount_positive"),
        {"comment": "Расходы садоводческих товариществ (ремонт, зарплата, материалы)"},
    )

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    cooperative_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cooperatives.id"),
        nullable=False,
        index=True,
        comment="ID СТ, совершившего расход",
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("expense_categories.id"),
        nullable=False,
        index=True,
        comment="ID категории расхода",
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    document_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
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

    cooperative: Mapped["Cooperative"] = relationship("Cooperative", back_populates="expenses")
    category: Mapped["ExpenseCategory"] = relationship("ExpenseCategory", back_populates="expenses")
