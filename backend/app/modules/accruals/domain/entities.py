"""Accruals domain entities.

Pure Python - no framework dependencies (FastAPI, SQLAlchemy, Pydantic).
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.modules.shared.kernel.exceptions import DomainError


@dataclass
class ContributionType:
    """Вид взноса — справочник типов начислений.

    Используется для классификации начислений (Accrual):
    - Членский взнос — регулярные платежи членов СТ
    - Целевой взнос — на конкретные цели (ремонт, благоустройство)
    - Взнос за электричество — оплата электроэнергии
    - Взнос за воду — оплата водоснабжения
    - Другие виды взносов
    """

    name: str
    code: str
    description: str | None = None
    is_system: bool = False
    created_at: datetime | None = None
    id: UUID | None = None


@dataclass
class Accrual:
    """Начисление по финансовому субъекту.

    Представляет собой задолженность по взносу или услуге за определённый период.
    Все начисления привязываются к FinancialSubject, а не напрямую к участку.
    Статусы: created (создано) → applied (применено) → cancelled (отменено).
    
    Attributes:
        due_date: Дата, до которой начисление должно быть оплачено. None — срок не установлен.
    """

    financial_subject_id: UUID
    contribution_type_id: UUID
    amount: Decimal
    accrual_date: date
    period_start: date
    period_end: date | None
    due_date: date | None = None
    status: str = "created"  # created, applied, cancelled
    created_at: datetime | None = None
    updated_at: datetime | None = None
    id: UUID | None = None
    cancelled_at: datetime | None = None
    cancelled_by_user_id: UUID | None = None
    cancellation_reason: str | None = None
    operation_number: str = ""

    def cancel(self, cancelled_by: UUID, reason: str | None, now: datetime) -> None:
        """Отменить начисление.

        Args:
            cancelled_by: ID пользователя, отменившего начисление.
            reason: Причина отмены (опционально).
            now: Текущая дата и время.

        Raises:
            DomainError: Если начисление уже отменено.
        """
        if self.status == "cancelled":
            raise DomainError("Accrual is already cancelled")

        self.status = "cancelled"
        self.cancelled_at = now
        self.cancelled_by_user_id = cancelled_by
        self.cancellation_reason = reason or None
