"""Domain events for financial_core module.

Pure Python - no framework dependencies.
"""

from dataclasses import dataclass
from uuid import UUID

from app.modules.shared.kernel.events import DomainEvent


@dataclass
class FinancialSubjectCreated(DomainEvent):
    """Event published when a FinancialSubject is created."""

    financial_subject_id: UUID
    subject_type: str
    subject_id: UUID
    cooperative_id: UUID
    code: str


@dataclass
class BalanceUpdated(DomainEvent):
    """Event published when balance is updated."""

    financial_subject_id: UUID
    new_balance: float  # Serialized Decimal
    total_accruals: float
    total_payments: float
