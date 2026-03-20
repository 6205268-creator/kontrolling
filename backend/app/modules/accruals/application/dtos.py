"""DTOs for accruals application layer."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AccrualBase(BaseModel):
    """Base schema for Accrual."""

    financial_subject_id: UUID = Field(..., description="ID финансового субъекта")
    contribution_type_id: UUID = Field(..., description="ID вида взноса")
    amount: Decimal = Field(..., description="Сумма начисления", ge=0, decimal_places=2)
    accrual_date: date = Field(..., description="Дата начисления")
    period_start: date = Field(..., description="Начало периода")
    period_end: date | None = Field(None, description="Конец периода")
    due_date: date | None = Field(None, description="Срок оплаты")


class AccrualCreate(AccrualBase):
    """Schema for creating an Accrual."""

    pass


class AccrualUpdate(BaseModel):
    """Schema for updating an Accrual."""

    amount: Decimal | None = Field(None, description="Сумма начисления", ge=0, decimal_places=2)
    period_end: date | None = Field(None, description="Конец периода")


class AccrualInDB(AccrualBase):
    """Schema for Accrual with DB fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str = Field(..., description="Статус (created, applied, cancelled)")
    created_at: datetime
    updated_at: datetime
    cancelled_at: datetime | None = None
    cancelled_by_user_id: UUID | None = None
    cancellation_reason: str | None = None
    operation_number: str = Field(..., description="Уникальный номер операции")
    due_date: date | None = Field(None, description="Срок оплаты")


class AccrualBatchCreate(BaseModel):
    """Schema for batch creation of accruals."""

    accruals: list[AccrualCreate] = Field(..., description="Список начислений для создания")


class ContributionTypeInDB(BaseModel):
    """Schema for ContributionType with DB fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="ID вида взноса")
    name: str = Field(..., description="Название")
    code: str = Field(..., description="Код")
    description: str | None = Field(None, description="Описание")
