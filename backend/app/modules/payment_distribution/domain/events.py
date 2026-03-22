"""Payment Distribution domain events."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.modules.shared.kernel.events import DomainEvent


@dataclass
class MemberCreated(DomainEvent):
    """Event published when a new member is created."""

    member_id: UUID
    owner_id: UUID
    cooperative_id: UUID
    occurred_at: datetime


@dataclass
class PersonalAccountOpened(DomainEvent):
    """Event published when a personal account is opened."""

    account_id: UUID
    member_id: UUID
    account_number: str
    occurred_at: datetime


@dataclass
class PaymentCredited(DomainEvent):
    """Event published when payment is credited to personal account."""

    transaction_id: UUID
    account_id: UUID
    payment_id: UUID
    amount: Decimal
    occurred_at: datetime


@dataclass
class PaymentDistributed(DomainEvent):
    """Event published when payment is distributed to debt."""

    distribution_id: UUID
    payment_id: UUID
    financial_subject_id: UUID
    accrual_id: UUID | None
    amount: Decimal
    priority: int
    occurred_at: datetime


@dataclass
class PaymentRefunded(DomainEvent):
    """Event published when payment distribution is reversed."""

    distribution_id: UUID
    amount: Decimal
    occurred_at: datetime
    accrual_id: UUID | None = None
    financial_subject_id: UUID | None = None


@dataclass
class DebtPartiallyPaid(DomainEvent):
    """Event published when debt is partially paid."""

    financial_subject_id: UUID
    accrual_id: UUID | None
    paid_amount: Decimal
    remaining_balance: Decimal
    occurred_at: datetime


@dataclass
class DebtFullyPaid(DomainEvent):
    """Event published when debt is fully paid."""

    financial_subject_id: UUID
    accrual_id: UUID | None
    paid_amount: Decimal
    occurred_at: datetime
