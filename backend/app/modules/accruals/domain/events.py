"""Accruals domain events.

Pure Python - no framework dependencies.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.modules.shared.kernel.events import DomainEvent


@dataclass(kw_only=True)
class AccrualApplied(DomainEvent):
    """Event published when an Accrual is applied (status: created → applied)."""

    accrual_id: UUID
    financial_subject_id: UUID
    contribution_type_id: UUID
    amount: Decimal
    accrual_date: date
    operation_number: str


@dataclass(kw_only=True)
class AccrualCancelled(DomainEvent):
    """Event published when an Accrual is cancelled."""

    accrual_id: UUID
    cancelled_at: datetime
    cancelled_by: UUID
    reason: str | None
