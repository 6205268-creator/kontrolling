"""Payments domain entities.

Pure Python - no framework dependencies.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.modules.shared.kernel.entities import BaseEntity


@dataclass
class Payment(BaseEntity):
    """Платёж по финансовому субъекту.

    Представляет собой поступление денежных средств от владельца (Owner)
    в счёт погашения задолженности финансового субъекта.
    Статусы: confirmed (подтверждён) → cancelled (отменён).
    """

    financial_subject_id: UUID
    payer_owner_id: UUID
    amount: Decimal
    payment_date: date
    document_number: str | None = None
    description: str | None = None
    status: str = "confirmed"  # confirmed, cancelled
    created_at: datetime | None = None
    updated_at: datetime | None = None
