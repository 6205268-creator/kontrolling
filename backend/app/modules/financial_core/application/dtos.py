"""DTOs for financial_core application layer."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FinancialSubjectBase(BaseModel):
    """Base schema for FinancialSubject."""

    subject_type: str = Field(
        ...,
        description="Тип субъекта",
        pattern="^(LAND_PLOT|WATER_METER|ELECTRICITY_METER|GENERAL_DECISION)$",
    )
    subject_id: UUID = Field(..., description="ID бизнес-объекта")
    cooperative_id: UUID = Field(..., description="ID coopérative")
    code: str = Field(..., description="Уникальный код", min_length=1, max_length=50)
    status: str = Field("active", description="Статус", pattern="^(active|closed)$")


class FinancialSubjectCreate(FinancialSubjectBase):
    """Schema for creating a FinancialSubject."""

    pass


class FinancialSubjectInDB(FinancialSubjectBase):
    """Schema for FinancialSubject with DB fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


class BalanceInfo(BaseModel):
    """
    Information about balance of a financial subject.

    balance = total_accruals - total_payments
    Positive balance means debt (more accrued than paid).
    """

    financial_subject_id: UUID = Field(..., description="ID финансового субъекта")
    subject_type: str = Field(..., description="Тип субъекта (LAND_PLOT, WATER_METER, etc.)")
    subject_id: UUID = Field(..., description="ID бизнес-объекта (участок, счётчик, etc.)")
    cooperative_id: UUID = Field(..., description="ID СТ")
    code: str = Field(..., description="Код финансового субъекта для платёжных документов")
    total_accruals: Decimal = Field(
        ..., description="Сумма всех начислений (applied)", decimal_places=2
    )
    total_payments: Decimal = Field(
        ..., description="Сумма всех платежей (confirmed)", decimal_places=2
    )
    balance: Decimal = Field(
        ..., description="Задолженность (accruals - payments)", decimal_places=2
    )


class FinancialSubjectInfo(BaseModel):
    """Information about financial subject without balance."""

    id: UUID
    subject_type: str
    subject_id: UUID
    cooperative_id: UUID
    code: str
    status: str
