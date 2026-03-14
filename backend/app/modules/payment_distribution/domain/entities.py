"""
Domain entities for Payment Distribution module.

Чистые Python-объекты без зависимостей от фреймворков.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID


@dataclass
class Member:
    """Член СТ (садоводческого товарищества)."""

    id: UUID
    owner_id: UUID
    cooperative_id: UUID
    status: str  # "active" | "expelled" | "resigned"
    joined_date: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MemberPlot:
    """Участок члена СТ."""

    id: UUID
    member_id: UUID
    land_plot_id: UUID
    share_numerator: int
    share_denominator: int
    is_primary: bool
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PersonalAccount:
    """Лицевой счёт члена СТ."""

    id: UUID
    member_id: UUID
    cooperative_id: UUID
    account_number: str
    balance: Decimal
    status: str  # "active" | "closed" | "blocked"
    opened_at: datetime
    closed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PersonalAccountTransaction:
    """Операция по лицевому счёту."""

    id: UUID
    account_id: UUID
    payment_id: Optional[UUID]
    distribution_id: Optional[UUID]
    transaction_number: str
    transaction_date: datetime
    amount: Decimal
    type: str  # "payment_received" | "distribution" | "refund" | "adjustment"
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PaymentDistribution:
    """Распределение платежа по финансовому субъекту."""

    id: UUID
    payment_id: UUID
    financial_subject_id: UUID
    distribution_number: str
    distributed_at: datetime
    amount: Decimal
    priority: int
    status: str  # "pending" | "applied" | "partial" | "cancelled"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SettingsModule:
    """Модуль настроек."""

    id: UUID
    cooperative_id: UUID
    module_name: str  # "payment_distribution" | "contribution_types" | "meter_tariffs"
    is_active: bool
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PaymentDistributionRule:
    """Правило распределения платежей."""

    id: UUID
    settings_module_id: UUID
    rule_type: str  # "membership" | "target" | "additional" | "meter_water" | "meter_electricity"
    priority: int
    contribution_type_id: Optional[UUID] = None
    meter_type: Optional[str] = None  # "water" | "electricity"
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ContributionTypeSettings:
    """Настройки вида взноса."""

    id: UUID
    settings_module_id: UUID
    contribution_type_id: UUID
    default_amount: Optional[Decimal] = None
    is_mandatory: bool = True
    calculation_period: str = "year"  # "month" | "quarter" | "year"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MeterTariff:
    """Тариф на ресурсы."""

    id: UUID
    settings_module_id: UUID
    meter_type: str  # "water" | "electricity" | "gas"
    tariff_per_unit: Decimal
    valid_from: datetime
    valid_to: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
