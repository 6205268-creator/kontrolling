"""Domain services for reporting."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class CashFlowReport:
    """Cash flow report for a period."""

    period_start: date
    period_end: date
    total_accruals: Decimal
    total_payments: Decimal
    total_expenses: Decimal
    net_balance: Decimal


@dataclass
class DebtorInfo:
    """Debtor information for report."""

    financial_subject_id: str  # UUID as string
    subject_type: str
    subject_info: dict
    owner_name: str
    total_debt: Decimal
    overdue_days: int = 0
    penalty_amount: Decimal = Decimal("0.00")
    total_with_penalty: Decimal = Decimal("0.00")
