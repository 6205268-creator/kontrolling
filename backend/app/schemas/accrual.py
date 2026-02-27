from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AccrualBase(BaseModel):
    """Базовая схема Accrual."""

    financial_subject_id: UUID = Field(..., description="ID финансового субъекта")
    contribution_type_id: UUID = Field(..., description="ID вида взноса")
    amount: Decimal = Field(..., description="Сумма начисления", ge=0, decimal_places=2)
    accrual_date: date = Field(..., description="Дата начисления")
    period_start: date = Field(..., description="Начало периода")
    period_end: date | None = Field(None, description="Конец периода")


class AccrualCreate(AccrualBase):
    """Схема для создания Accrual."""

    pass


class AccrualUpdate(BaseModel):
    """Схема для обновления Accrual."""

    amount: Decimal | None = Field(None, description="Сумма начисления", ge=0, decimal_places=2)
    period_end: date | None = Field(None, description="Конец периода")


class AccrualInDB(AccrualBase):
    """Схема Accrual с полями БД."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str = Field(..., description="Статус (created, applied, cancelled)")
    created_at: datetime
    updated_at: datetime


class AccrualBatchCreate(BaseModel):
    """Схема для массового создания начислений."""

    accruals: list[AccrualCreate] = Field(..., description="Список начислений для создания")
