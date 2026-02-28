"""DTOs for expenses module."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExpenseCategoryBase(BaseModel):
    """Base schema for ExpenseCategory."""

    name: str = Field(..., description="Название категории", min_length=1, max_length=255)
    code: str = Field(..., description="Код категории", min_length=1, max_length=30)
    description: str | None = Field(None, description="Описание", max_length=512)


class ExpenseCategoryInDB(ExpenseCategoryBase):
    """Schema for ExpenseCategory with DB fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


class ExpenseBase(BaseModel):
    """Base schema for Expense."""

    cooperative_id: UUID = Field(..., description="ID СТ")
    category_id: UUID = Field(..., description="ID категории расхода")
    amount: Decimal = Field(..., description="Сумма расхода", gt=0, decimal_places=2)
    expense_date: date = Field(..., description="Дата расхода")
    document_number: str | None = Field(None, description="Номер документа", max_length=50)
    description: str | None = Field(None, description="Описание", max_length=512)


class ExpenseCreate(ExpenseBase):
    """Schema for creating an Expense."""

    pass


class ExpenseUpdate(BaseModel):
    """Schema for updating an Expense."""

    category_id: UUID | None = Field(None, description="ID категории расхода")
    amount: Decimal | None = Field(None, description="Сумма расхода", gt=0, decimal_places=2)
    document_number: str | None = Field(None, description="Номер документа", max_length=50)
    description: str | None = Field(None, description="Описание", max_length=512)


class ExpenseInDB(ExpenseBase):
    """Schema for Expense with DB fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str = Field(..., description="Статус (created, confirmed, cancelled)")
    created_at: datetime
    updated_at: datetime
