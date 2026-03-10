"""Financial Core domain entities.

Pure Python - no framework dependencies (FastAPI, SQLAlchemy, Pydantic).
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.modules.shared.kernel.entities import BaseEntity


@dataclass
class FinancialSubject(BaseEntity):
    """Финансовый субъект — центр финансовой ответственности.

    Ключевая концепция: все начисления (Accrual) и платежи (Payment)
    привязываются к FinancialSubject, а не напрямую к бизнес-объектам.
    Это позволяет единообразно работать с разными типами обязательств:
    - LAND_PLOT — земельный участок
    - WATER_METER — счётчик воды
    - ELECTRICITY_METER — счётчик электроэнергии
    - GENERAL_DECISION — решение общего собрания
    """

    subject_type: str  # LAND_PLOT, WATER_METER, ELECTRICITY_METER, GENERAL_DECISION
    subject_id: UUID
    cooperative_id: UUID
    code: str
    status: str = "active"  # active, closed
    created_at: datetime | None = None


@dataclass
class Balance:
    """Value object representing balance of a FinancialSubject.

    balance = total_accruals - total_payments
    Positive balance means debt (more accrued than paid).
    """

    financial_subject_id: UUID
    subject_type: str
    subject_id: UUID
    cooperative_id: UUID
    code: str
    total_accruals: Decimal
    total_payments: Decimal
    balance: Decimal = field(init=False)

    def __post_init__(self):
        self.balance = self.total_accruals - self.total_payments

    @property
    def is_in_debt(self) -> bool:
        """Check if subject has debt (positive balance)."""
        return self.balance > 0

    @property
    def has_credit(self) -> bool:
        """Check if subject has overpayment (negative balance)."""
        return self.balance < 0

    @property
    def is_balanced(self) -> bool:
        """Check if subject balance is zero."""
        return self.balance == Decimal("0.00")
