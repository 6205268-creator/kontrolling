"""Модели таблиц истории изменений для аудита критичных сущностей.

Заполняются через SQLAlchemy event listeners при insert/update/delete
у PlotOwnership, Accrual, Payment, Expense. FK на исходные таблицы не ставим,
чтобы история сохранялась при удалении записи.
"""
from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Guid


def _history_primary_key() -> Mapped[uuid.UUID]:
    return mapped_column(Guid(), primary_key=True, default=uuid.uuid4)


class PlotOwnershipHistory(Base):
    """История изменений прав собственности на участок."""

    __tablename__ = "plot_ownerships_history"
    __table_args__ = {"comment": "Аудит изменений прав собственности на участки"}

    id: Mapped[uuid.UUID] = _history_primary_key()
    entity_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False, index=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    operation: Mapped[str] = mapped_column(String(10), nullable=False)

    land_plot_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False)
    share_numerator: Mapped[int] = mapped_column(Integer, nullable=False)
    share_denominator: Mapped[int] = mapped_column(Integer, nullable=False)
    is_primary: Mapped[bool] = mapped_column(nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AccrualHistory(Base):
    """История изменений начислений."""

    __tablename__ = "accruals_history"
    __table_args__ = {"comment": "Аудит изменений начислений"}

    id: Mapped[uuid.UUID] = _history_primary_key()
    entity_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False, index=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    operation: Mapped[str] = mapped_column(String(10), nullable=False)

    financial_subject_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False)
    contribution_type_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    accrual_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PaymentHistory(Base):
    """История изменений платежей."""

    __tablename__ = "payments_history"
    __table_args__ = {"comment": "Аудит изменений платежей"}

    id: Mapped[uuid.UUID] = _history_primary_key()
    entity_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False, index=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    operation: Mapped[str] = mapped_column(String(10), nullable=False)

    financial_subject_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False)
    payer_owner_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    document_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ExpenseHistory(Base):
    """История изменений расходов."""

    __tablename__ = "expenses_history"
    __table_args__ = {"comment": "Аудит изменений расходов"}

    id: Mapped[uuid.UUID] = _history_primary_key()
    entity_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False, index=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    operation: Mapped[str] = mapped_column(String(10), nullable=False)

    cooperative_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    document_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
