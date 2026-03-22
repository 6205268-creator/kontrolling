"""Pydantic schemas for reporting API."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class DebtorInfo(BaseModel):
    """Information about a debtor for report."""

    financial_subject_id: UUID = Field(..., description="ID финансового субъекта")
    subject_type: str = Field(..., description="Тип субъекта")
    subject_info: dict = Field(..., description="Информация о бизнес-объекте")
    owner_name: str = Field(..., description="ФИО владельца")
    total_debt: Decimal = Field(..., description="Сумма задолженности", decimal_places=2)
    overdue_days: int = Field(0, description="Дней просрочки (для расчёта пеней)")
    penalty_amount: Decimal = Field(Decimal("0.00"), description="Расчётные пени", decimal_places=2)
    total_with_penalty: Decimal = Field(
        Decimal("0.00"),
        description="Итого долг + пени",
        decimal_places=2,
    )


class CashFlowReport(BaseModel):
    """Cash flow report for a period."""

    period_start: date = Field(..., description="Начало отчётного периода")
    period_end: date = Field(..., description="Конец отчётного периода")
    total_accruals: Decimal = Field(..., description="Сумма начислений", decimal_places=2)
    total_payments: Decimal = Field(..., description="Сумма платежей", decimal_places=2)
    total_expenses: Decimal = Field(..., description="Сумма расходов", decimal_places=2)
    net_balance: Decimal = Field(..., description="Чистый баланс", decimal_places=2)


class TurnoverSheetRowOut(BaseModel):
    """Строка оборотной ведомости."""

    financial_subject_id: UUID = Field(..., description="ID финансового субъекта")
    code: str = Field(..., description="Код субъекта")
    opening_balance: Decimal = Field(..., description="Сальдо на начало", decimal_places=2)
    accrued_in_period: Decimal = Field(..., description="Начислено за период", decimal_places=2)
    paid_in_period: Decimal = Field(..., description="Оплачено за период", decimal_places=2)
    closing_balance: Decimal = Field(..., description="Сальдо на конец", decimal_places=2)
