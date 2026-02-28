"""Expenses domain entities."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.modules.shared.kernel.entities import BaseEntity


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
