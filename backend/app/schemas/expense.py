from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExpenseCategoryBase(BaseModel):
    """Базовая схема ExpenseCategory."""

    name: str = Field(..., description="Название категории", min_length=1, max_length=255)
    code: str = Field(..., description="Код категории", min_length=1, max_length=30)
    description: str | None = Field(None, description="Описание", max_length=512)


class ExpenseCategoryCreate(ExpenseCategoryBase):
    """Схема для создания ExpenseCategory."""

    pass


class ExpenseCategoryInDB(ExpenseCategoryBase):
    """Схема ExpenseCategory с полями БД."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


class ExpenseBase(BaseModel):
    """Базовая схема Expense."""

    cooperative_id: UUID = Field(..., description="ID СТ")
    category_id: UUID = Field(..., description="ID категории расхода")
    amount: Decimal = Field(..., description="Сумма расхода", gt=0, decimal_places=2)
    expense_date: date = Field(..., description="Дата расхода")
    document_number: str | None = Field(None, description="Номер документа", max_length=50)
    description: str | None = Field(None, description="Описание", max_length=512)


class ExpenseCreate(ExpenseBase):
    """Схема для создания Expense."""

    pass


class ExpenseUpdate(BaseModel):
    """Схема для обновления Expense."""

    category_id: UUID | None = Field(None, description="ID категории расхода")
    amount: Decimal | None = Field(None, description="Сумма расхода", gt=0, decimal_places=2)
    document_number: str | None = Field(None, description="Номер документа", max_length=50)
    description: str | None = Field(None, description="Описание", max_length=512)


class ExpenseInDB(ExpenseBase):
    """Схема Expense с полями БД."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str = Field(..., description="Статус (created, confirmed, cancelled)")
    created_at: datetime
    updated_at: datetime
