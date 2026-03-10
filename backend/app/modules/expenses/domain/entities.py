"""Expenses domain entities."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.modules.shared.kernel.entities import BaseEntity
from app.modules.shared.kernel.exceptions import DomainError


@dataclass
class ExpenseCategory(BaseEntity):
    """Категория расходов СТ — справочник."""

    name: str
    code: str
    description: str | None = None
    created_at: datetime | None = None


@dataclass
class Expense(BaseEntity):
    """Расход садоводческого товарищества."""

    cooperative_id: UUID
    category_id: UUID
    amount: Decimal
    expense_date: date
    document_number: str | None = None
    description: str | None = None
    status: str = "created"  # created, confirmed, cancelled
    created_at: datetime | None = None
    updated_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancelled_by_user_id: UUID | None = None
    cancellation_reason: str | None = None
    operation_number: str = ""

    def cancel(self, cancelled_by: UUID, reason: str | None, now: datetime) -> None:
        """Отменить расход.

        Args:
            cancelled_by: ID пользователя, отменившего расход.
            reason: Причина отмены (опционально).
            now: Текущая дата и время.

        Raises:
            DomainError: Если расход уже отменён.
        """
        if self.status == "cancelled":
            raise DomainError("Expense is already cancelled")

        self.status = "cancelled"
        self.cancelled_at = now
        self.cancelled_by_user_id = cancelled_by
        self.cancellation_reason = reason or None
