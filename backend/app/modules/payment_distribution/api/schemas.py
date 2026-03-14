"""
API schemas for Payment Distribution module.

Pydantic schemas for request/response validation.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# Member Schemas
# =============================================================================


class MemberCreate(BaseModel):
    """Создание члена СТ."""

    owner_id: UUID
    cooperative_id: UUID
    joined_date: datetime


class MemberResponse(BaseModel):
    """Ответ: член СТ."""

    id: UUID
    owner_id: UUID
    cooperative_id: UUID
    status: str
    joined_date: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemberPlotResponse(BaseModel):
    """Ответ: участок члена СТ."""

    id: UUID
    member_id: UUID
    land_plot_id: UUID
    share_numerator: int
    share_denominator: int
    is_primary: bool

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Personal Account Schemas
# =============================================================================


class PersonalAccountResponse(BaseModel):
    """Ответ: лицевой счёт."""

    id: UUID
    member_id: UUID
    cooperative_id: UUID
    account_number: str
    balance: Decimal
    status: str
    opened_at: datetime
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PersonalAccountTransactionResponse(BaseModel):
    """Ответ: операция по счёту."""

    id: UUID
    account_id: UUID
    transaction_number: str
    transaction_date: datetime
    amount: Decimal
    type: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AccountAdjustmentCreate(BaseModel):
    """Корректировка счёта."""

    amount: Decimal = Field(..., description="Сумма (+ для прихода, - для расхода)")
    type: str = Field(..., description="Тип операции: adjustment | refund")
    description: Optional[str] = None
    transaction_date: Optional[datetime] = None


# =============================================================================
# Payment Schemas
# =============================================================================


class PaymentCreate(BaseModel):
    """Создание платежа."""

    from_owner_id: UUID
    total_amount: Decimal = Field(..., gt=0, description="Сумма платежа (должна быть > 0)")
    payment_date: datetime
    document_number: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)


class PaymentDistributionResponse(BaseModel):
    """Ответ: распределение платежа."""

    id: UUID
    payment_id: UUID
    financial_subject_id: UUID
    distribution_number: str
    distributed_at: datetime
    amount: Decimal
    priority: int
    status: str

    model_config = ConfigDict(from_attributes=True)


class PaymentResponse(BaseModel):
    """Ответ: платёж."""

    id: UUID
    from_owner_id: UUID
    total_amount: Decimal
    payment_date: datetime
    document_number: Optional[str] = None
    description: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    distributions: List[PaymentDistributionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PaymentCancel(BaseModel):
    """Отмена платежа."""

    reason: str = Field(..., min_length=1, max_length=500)


# =============================================================================
# Settings Schemas
# =============================================================================


class PaymentDistributionRuleCreate(BaseModel):
    """Создание правила распределения."""

    rule_type: str = Field(
        ...,
        description="Тип правила: membership | target | additional | meter_water | meter_electricity",
    )
    priority: int = Field(..., gt=0, description="Приоритет (1 = высший)")
    contribution_type_id: Optional[UUID] = None
    meter_type: Optional[str] = Field(None, description="water | electricity")


class PaymentDistributionRuleResponse(BaseModel):
    """Ответ: правило распределения."""

    id: UUID
    settings_module_id: UUID
    rule_type: str
    priority: int
    contribution_type_id: Optional[UUID] = None
    meter_type: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SettingsModuleResponse(BaseModel):
    """Ответ: модуль настроек."""

    id: UUID
    cooperative_id: UUID
    module_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContributionTypeSettingsCreate(BaseModel):
    """Создание настройки вида взноса."""

    contribution_type_id: UUID
    default_amount: Optional[Decimal] = None
    is_mandatory: bool = True
    calculation_period: str = "year"


class ContributionTypeSettingsResponse(BaseModel):
    """Ответ: настройка вида взноса."""

    id: UUID
    settings_module_id: UUID
    contribution_type_id: UUID
    default_amount: Optional[Decimal] = None
    is_mandatory: bool
    calculation_period: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeterTariffCreate(BaseModel):
    """Создание тарифа на ресурсы."""

    meter_type: str = Field(..., description="water | electricity | gas")
    tariff_per_unit: Decimal = Field(..., gt=0)
    valid_from: datetime
    valid_to: Optional[datetime] = None


class MeterTariffResponse(BaseModel):
    """Ответ: тариф на ресурсы."""

    id: UUID
    settings_module_id: UUID
    meter_type: str
    tariff_per_unit: Decimal
    valid_from: datetime
    valid_to: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
