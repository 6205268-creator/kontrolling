"""
Domain events for Payment Distribution module.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID


@dataclass
class MemberCreated:
    """Создан член СТ."""

    member_id: UUID
    owner_id: UUID
    cooperative_id: UUID
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PersonalAccountOpened:
    """Открыт лицевой счёт."""

    account_id: UUID
    member_id: UUID
    cooperative_id: UUID
    account_number: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PaymentReceived:
    """Получен платёж."""

    payment_id: UUID
    owner_id: UUID
    account_id: UUID
    amount: Decimal
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PaymentDistributed:
    """Платёж распределён по задолженностям."""

    payment_id: UUID
    distributions: List[UUID]
    total_distributed: Decimal
    remaining_balance: Decimal
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PaymentCancelled:
    """Платёж отменён."""

    payment_id: UUID
    reason: str
    reversed_amount: Decimal
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DistributionRuleCreated:
    """Создано правило распределения."""

    rule_id: UUID
    cooperative_id: UUID
    rule_type: str
    priority: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DistributionRuleUpdated:
    """Обновлено правило распределения."""

    rule_id: UUID
    cooperative_id: UUID
    changes: dict
    timestamp: datetime = field(default_factory=datetime.utcnow)
