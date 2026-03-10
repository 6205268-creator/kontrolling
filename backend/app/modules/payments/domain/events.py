"""Payments domain events.

Pure Python - no framework dependencies.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.modules.shared.kernel.events import DomainEvent


@dataclass(kw_only=True)
class PaymentConfirmed(DomainEvent):
    """Event published when a Payment is confirmed (created)."""

    payment_id: UUID
    financial_subject_id: UUID
    payer_owner_id: UUID
    amount: Decimal
    payment_date: date
    operation_number: str


@dataclass(kw_only=True)
class PaymentCancelled(DomainEvent):
    """Event published when a Payment is cancelled."""

    payment_id: UUID
    cancelled_at: datetime
    cancelled_by: UUID
    reason: str | None
