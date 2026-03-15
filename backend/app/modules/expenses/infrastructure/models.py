"""Expenses SQLAlchemy models."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Guid

if TYPE_CHECKING:
    from app.modules.cooperative_core.infrastructure.models import CooperativeModel


class ExpenseModel(Base):
    """SQLAlchemy model for Expense."""

    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_expenses_amount_positive"),
        {
            "comment": "Расходы садоводческих товариществ (ремонт, зарплата, материалы)",
            "extend_existing": True,
        },
    )

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    cooperative_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cooperatives.id"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("expense_categories.id"),
        nullable=False,
        index=True,
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
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Guid(), ForeignKey("app_users.id"), nullable=True
    )
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    operation_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Relationships
    cooperative: Mapped["CooperativeModel"] = relationship(
        "CooperativeModel", back_populates="expenses"
    )

    def to_domain(self) -> "Expense":
        """Convert to domain entity."""
        from app.modules.expenses.domain.entities import Expense

        return Expense(
            id=self.id,
            cooperative_id=self.cooperative_id,
            category_id=self.category_id,
            amount=self.amount,
            expense_date=self.expense_date,
            document_number=self.document_number,
            description=self.description,
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at,
            cancelled_at=self.cancelled_at,
            cancelled_by_user_id=self.cancelled_by_user_id,
            cancellation_reason=self.cancellation_reason,
            operation_number=self.operation_number,
        )

    @classmethod
    def from_domain(cls, entity: "Expense") -> "ExpenseModel":
        """Create from domain entity."""
        return cls(
            id=entity.id,
            cooperative_id=entity.cooperative_id,
            category_id=entity.category_id,
            amount=entity.amount,
            expense_date=entity.expense_date,
            document_number=entity.document_number,
            description=entity.description,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            cancelled_at=entity.cancelled_at,
            cancelled_by_user_id=entity.cancelled_by_user_id,
            cancellation_reason=entity.cancellation_reason,
            operation_number=entity.operation_number,
        )


class ExpenseHistoryModel(Base):
    """SQLAlchemy model for Expense history."""

    __tablename__ = "expenses_history"
    __table_args__ = {"comment": "Аудит изменений расходов", "extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
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
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_by_user_id: Mapped[uuid.UUID | None] = mapped_column(Guid(), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    operation_number: Mapped[str | None] = mapped_column(String(50), nullable=True)


class ExpenseCategoryModel(Base):
    """SQLAlchemy model for ExpenseCategory."""

    __tablename__ = "expense_categories"
    __table_args__ = {
        "comment": "Справочник категорий расходов СТ (дороги, зарплата, материалы)",
        "extend_existing": True,
    }

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> "ExpenseCategory":
        """Convert to domain entity."""
        from app.modules.expenses.domain.entities import ExpenseCategory

        return ExpenseCategory(
            id=self.id,
            name=self.name,
            code=self.code,
            description=self.description,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: "ExpenseCategory") -> "ExpenseCategoryModel":
        """Create from domain entity."""
        return cls(
            id=entity.id,
            name=entity.name,
            code=entity.code,
            description=entity.description,
            created_at=entity.created_at,
        )
