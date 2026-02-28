from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class BalanceInfo(BaseModel):
    """
    Информация о балансе финансового субъекта.

    balance = total_accruals - total_payments
    Положительный balance означает задолженность (начислено больше чем оплачено).
    """

    financial_subject_id: UUID = Field(..., description="ID финансового субъекта")
    subject_type: str = Field(..., description="Тип субъекта (LAND_PLOT, WATER_METER, etc.)")
    subject_id: UUID = Field(..., description="ID бизнес-объекта (участок, счётчик, etc.)")
    cooperative_id: UUID = Field(..., description="ID СТ")
    code: str = Field(..., description="Код финансового субъекта для платёжных документов")
    total_accruals: Decimal = Field(
        ..., description="Сумма всех начислений (applied)", decimal_places=2
    )
    total_payments: Decimal = Field(
        ..., description="Сумма всех платежей (confirmed)", decimal_places=2
    )
    balance: Decimal = Field(
        ..., description="Задолженность (accruals - payments)", decimal_places=2
    )


class FinancialSubjectInfo(BaseModel):
    """Информация о финансовом субъекте без баланса."""

    id: UUID
    subject_type: str
    subject_id: UUID
    cooperative_id: UUID
    code: str
    status: str
