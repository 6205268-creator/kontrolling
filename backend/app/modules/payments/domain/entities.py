"""Payments domain entities.

Pure Python - no framework dependencies.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.modules.shared.kernel.entities import BaseEntity
from app.modules.shared.kernel.exceptions import DomainError


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
    cancelled_at: datetime | None = None
    cancelled_by_user_id: UUID | None = None
    cancellation_reason: str | None = None
    operation_number: str = ""

    def cancel(self, cancelled_by: UUID, reason: str | None, now: datetime) -> None:
        """Отменить платёж.

        Args:
            cancelled_by: ID пользователя, отменившего платёж.
            reason: Причина отмены (опционально).
            now: Текущая дата и время.

        Raises:
            DomainError: Если платёж уже отменён.
        """
        if self.status == "cancelled":
            raise DomainError("Payment is already cancelled")

        self.status = "cancelled"
        self.cancelled_at = now
        self.cancelled_by_user_id = cancelled_by
        self.cancellation_reason = reason or None
