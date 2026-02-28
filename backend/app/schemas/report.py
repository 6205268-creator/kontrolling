from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class DebtorInfo(BaseModel):
    """
    Информация о должнике для отчёта.

    Содержит данные о финансовом субъекте с задолженностью,
    информацию о владельце и сумму долга.
    """

    financial_subject_id: UUID = Field(..., description="ID финансового субъекта")
    subject_type: str = Field(
        ..., description="Тип субъекта (LAND_PLOT, WATER_METER, ELECTRICITY_METER)"
    )
    subject_info: dict = Field(
        ..., description="Информация о бизнес-объекте (plot_number или meter serial)"
    )
    owner_name: str = Field(..., description="ФИО или название владельца")
    total_debt: Decimal = Field(..., description="Сумма задолженности (balance)", decimal_places=2)


class CashFlowReport(BaseModel):
    """
    Отчёт о движении денежных средств за период.

    Содержит суммы начислений, платежей и расходов за указанный период.
    """

    period_start: date = Field(..., description="Начало отчётного периода")
    period_end: date = Field(..., description="Конец отчётного периода")
    total_accruals: Decimal = Field(
        ..., description="Сумма всех начислений за период", decimal_places=2
    )
    total_payments: Decimal = Field(
        ..., description="Сумма всех платежей за период", decimal_places=2
    )
    total_expenses: Decimal = Field(
        ..., description="Сумма всех расходов за период", decimal_places=2
    )
    net_balance: Decimal = Field(
        ..., description="Чистый баланс (payments - expenses)", decimal_places=2
    )
