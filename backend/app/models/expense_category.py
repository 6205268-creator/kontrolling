from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Guid


class ExpenseCategory(Base):
    """Категория расходов СТ — справочник.

    Используется для классификации расходов (Expense):
    - Дороги — ремонт и содержание дорог
    - Зарплата — оплата труда председателя, бухгалтера и др.
    - Материалы — закупка стройматериалов
    - Услуги — сторонние услуги (вывоз мусора, охрана)
    - Налоги — налоговые платежи
    - Другие категории
    """

    __tablename__ = "expense_categories"
    __table_args__ = {"comment": "Справочник категорий расходов СТ (дороги, зарплата, материалы)"}

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    expenses: Mapped[list["Expense"]] = relationship("Expense", back_populates="category")
