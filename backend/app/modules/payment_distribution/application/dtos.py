"""
Application layer: Use Cases and DTOs for Payment Distribution module.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

# =============================================================================
# DTOs: Create / Input
# =============================================================================


@dataclass
class MemberCreateDTO:
    """Создание члена СТ."""

    owner_id: UUID
    cooperative_id: UUID
    joined_date: datetime


@dataclass
class PaymentCreateDTO:
    """Регистрация платежа."""

    from_owner_id: UUID
    total_amount: Decimal
    payment_date: datetime
    document_number: Optional[str] = None
    description: Optional[str] = None


@dataclass
class PaymentDistributeDTO:
    """Запуск распределения платежа."""

    payment_id: UUID


@dataclass
class PaymentCancelDTO:
    """Отмена платежа."""

    payment_id: UUID
    reason: str


@dataclass
class DistributionRuleCreateDTO:
    """Создание правила распределения."""

    cooperative_id: UUID
    rule_type: str  # "membership" | "target" | "additional" | "meter_water" | "meter_electricity"
    priority: int
    contribution_type_id: Optional[UUID] = None
    meter_type: Optional[str] = None


@dataclass
class ContributionTypeSettingsCreateDTO:
    """Создание настройки вида взноса."""

    settings_module_id: UUID
    contribution_type_id: UUID
    default_amount: Optional[Decimal] = None
    is_mandatory: bool = True
    calculation_period: str = "year"


@dataclass
class MeterTariffCreateDTO:
    """Создание тарифа на ресурсы."""

    settings_module_id: UUID
    meter_type: str  # "water" | "electricity" | "gas"
    tariff_per_unit: Decimal
    valid_from: datetime
    valid_to: Optional[datetime] = None


@dataclass
class AccountAdjustmentDTO:
    """Корректировка лицевого счёта."""

    account_id: UUID
    amount: Decimal
    type: str  # "adjustment" | "refund"
    description: Optional[str] = None
    transaction_date: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# DTOs: Response / Output
# =============================================================================


@dataclass
class MemberResponseDTO:
    """Ответ: член СТ."""

    id: UUID
    owner_id: UUID
    cooperative_id: UUID
    status: str
    joined_date: datetime
    created_at: datetime
    updated_at: datetime


@dataclass
class PersonalAccountResponseDTO:
    """Ответ: лицевой счёт."""

    id: UUID
    member_id: UUID
    cooperative_id: UUID
    account_number: str
    balance: Decimal
    status: str
    opened_at: datetime
    closed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class PersonalAccountTransactionResponseDTO:
    """Ответ: операция по счёту."""

    id: UUID
    account_id: UUID
    transaction_number: str
    transaction_date: datetime
    amount: Decimal
    type: str
    description: Optional[str]


@dataclass
class PaymentResponseDTO:
    """Ответ: платёж."""

    id: UUID
    from_owner_id: UUID
    total_amount: Decimal
    payment_date: datetime
    document_number: Optional[str]
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    distributions: List["PaymentDistributionResponseDTO"] = field(default_factory=list)


@dataclass
class PaymentDistributionResponseDTO:
    """Ответ: распределение платежа."""

    id: UUID
    payment_id: UUID
    financial_subject_id: UUID
    distribution_number: str
    distributed_at: datetime
    amount: Decimal
    priority: int
    status: str


@dataclass
class PaymentDistributionRuleResponseDTO:
    """Ответ: правило распределения."""

    id: UUID
    settings_module_id: UUID
    rule_type: str
    priority: int
    contribution_type_id: Optional[UUID]
    meter_type: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class SettingsModuleResponseDTO:
    """Ответ: модуль настроек."""

    id: UUID
    cooperative_id: UUID
    module_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class ContributionTypeSettingsResponseDTO:
    """Ответ: настройка вида взноса."""

    id: UUID
    settings_module_id: UUID
    contribution_type_id: UUID
    default_amount: Optional[Decimal]
    is_mandatory: bool
    calculation_period: str
    created_at: datetime
    updated_at: datetime


@dataclass
class MeterTariffResponseDTO:
    """Ответ: тариф на ресурсы."""

    id: UUID
    settings_module_id: UUID
    meter_type: str
    tariff_per_unit: Decimal
    valid_from: datetime
    valid_to: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Use Case Results
# =============================================================================


@dataclass
class DistributePaymentResult:
    """Результат распределения платежа."""

    payment_id: UUID
    distributions: List[PaymentDistributionResponseDTO]
    total_distributed: Decimal
    remaining_on_account: Decimal
    status: str  # "distributed" | "partial"


@dataclass
class CancelPaymentResult:
    """Результат отмены платежа."""

    payment_id: UUID
    reversed_amount: Decimal
    status: str  # "cancelled"
