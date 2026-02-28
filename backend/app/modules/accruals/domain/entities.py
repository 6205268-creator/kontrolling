"""Accruals domain entities.

Pure Python - no framework dependencies (FastAPI, SQLAlchemy, Pydantic).
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.modules.shared.kernel.entities import BaseEntity


@dataclass
class ContributionType(BaseEntity):
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
    created_at: datetime | None = None


@dataclass
class Accrual(BaseEntity):
    """Начисление по финансовому субъекту.

    Представляет собой задолженность по взносу или услуге за определённый период.
    Все начисления привязываются к FinancialSubject, а не напрямую к участку.
    Статусы: created (создано) → applied (применено) → cancelled (отменено).
    """

    financial_subject_id: UUID
    contribution_type_id: UUID
    amount: Decimal
    accrual_date: date
    period_start: date
    period_end: date | None
    status: str = "created"  # created, applied, cancelled
    created_at: datetime | None = None
    updated_at: datetime | None = None
