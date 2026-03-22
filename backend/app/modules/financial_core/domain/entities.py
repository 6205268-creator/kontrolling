"""Financial Core domain entities.

Pure Python - no framework dependencies (FastAPI, SQLAlchemy, Pydantic).
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from app.modules.shared.kernel.entities import BaseEntity
from app.modules.shared.kernel.money import Money


class PeriodType(StrEnum):
    """Type of financial period."""
    MONTHLY = "monthly"
    YEARLY = "yearly"


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
    total_accruals: Money
    total_payments: Money
    balance: Money = field(init=False)

    def __post_init__(self):
        self.balance = Money(self.total_accruals.amount - self.total_payments.amount)

    @property
    def is_in_debt(self) -> bool:
        """Check if subject has debt (positive balance)."""
        return self.balance.is_positive

    @property
    def has_credit(self) -> bool:
        """Check if subject has overpayment (negative balance)."""
        return self.balance.is_negative

    @property
    def is_balanced(self) -> bool:
        """Check if subject balance is zero."""
        return self.balance.is_zero


@dataclass
class FinancialPeriod:
    """Финансовый период — отчётный период для закрытия данных.

    Периоды используются для:
    - Контроля операций (нельзя менять закрытые периоды)
    - Формирования оборотных ведомостей
    - Снимков балансов (BalanceSnapshot)

    Статусы:
    - open: можно создавать/отменять операции
    - closed: только просмотр, казначей может переоткрыть в течение N дней
    - locked: только просмотр, переоткрытие только admin

    Атрибуты:
        id: Уникальный идентификатор.
        cooperative_id: ID садоводческого товарищества.
        period_type: Тип периода (monthly/yearly).
        year: Год периода.
        month: Месяц периода (1-12 для monthly, None для yearly).
        start_date: Первый день периода.
        end_date: Последний день периода.
        status: Статус периода (open/closed/locked).
        closed_at: Дата и время закрытия периода.
        closed_by_user_id: ID пользователя, закрывшего период.
        created_at: Дата создания записи.
    """

    cooperative_id: UUID
    period_type: PeriodType
    year: int
    month: int | None
    start_date: date
    end_date: date
    status: str = "open"  # open, closed, locked
    closed_at: datetime | None = None
    closed_by_user_id: UUID | None = None
    created_at: datetime | None = None
    id: UUID | None = None

    def close(self, closed_by: UUID, now: datetime) -> None:
        """Закрыть период.

        Args:
            closed_by: ID пользователя, закрывающего период.
            now: Текущая дата и время.

        Raises:
            ValueError: Если период уже закрыт или заблокирован.
        """
        if self.status != "open":
            raise ValueError(f"Cannot close period with status '{self.status}'")

        self.status = "closed"
        self.closed_at = now
        self.closed_by_user_id = closed_by

    def reopen(self, now: datetime) -> None:
        """Переоткрыть период (возвращает в статус open).

        Args:
            now: Текущая дата и время.

        Raises:
            ValueError: Если период не закрыт.
        """
        if self.status not in ("closed", "locked"):
            raise ValueError(f"Cannot reopen period with status '{self.status}'")

        self.status = "open"
        self.closed_at = None
        self.closed_by_user_id = None

    def lock(self) -> None:
        """Заблокировать период (переводит в статус locked).

        Raises:
            ValueError: Если период открыт.
        """
        if self.status == "open":
            raise ValueError("Cannot lock open period")

        self.status = "locked"

    @classmethod
    def create_monthly(cls, cooperative_id: UUID, year: int, month: int) -> "FinancialPeriod":
        """Создать месячный период.

        Args:
            cooperative_id: ID cooperative.
            year: Год.
            month: Месяц (1-12).

        Returns:
            Новый FinancialPeriod со статусом open.
        """
        if month < 1 or month > 12:
            raise ValueError(f"Month must be 1-12, got {month}")

        # Calculate start and end dates
        from calendar import monthrange
        day_start = 1
        day_end = monthrange(year, month)[1]
        start_date = date(year, month, day_start)
        end_date = date(year, month, day_end)

        return cls(
            cooperative_id=cooperative_id,
            period_type=PeriodType.MONTHLY,
            year=year,
            month=month,
            start_date=start_date,
            end_date=end_date,
            status="open",
        )

    @classmethod
    def create_yearly(cls, cooperative_id: UUID, year: int) -> "FinancialPeriod":
        """Создать годовой период.

        Args:
            cooperative_id: ID cooperative.
            year: Год.

        Returns:
            Новый FinancialPeriod со статусом open.
        """
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        return cls(
            cooperative_id=cooperative_id,
            period_type=PeriodType.YEARLY,
            year=year,
            month=None,
            start_date=start_date,
            end_date=end_date,
            status="open",
        )


@dataclass
class BalanceSnapshot:
    """Снимок баланса финансового субъекта на конец периода.

    Создаётся при закрытии периода для быстрого доступа к балансам.
    Не изменяется после создания (immutable).

    Атрибуты:
        id: Уникальный идентификатор.
        financial_subject_id: ID финансового субъекта.
        period_id: ID периода, на конец которого сделан снимок.
        cooperative_id: ID СТ (для индексации).
        total_accruals: Сумма всех начислений за период.
        total_payments: Сумма всех платежей за период.
        balance: Баланс на конец периода (total_accruals - total_payments).
        created_at: Дата создания снимка.
    """

    financial_subject_id: UUID
    period_id: UUID
    cooperative_id: UUID
    total_accruals: Money
    total_payments: Money
    balance: Money = field(init=False)
    created_at: datetime | None = None
    id: UUID | None = None

    def __post_init__(self):
        self.balance = Money(self.total_accruals.amount - self.total_payments.amount)


@dataclass
class DebtLine:
    """Строка долга по одному применённому начислению (фаза 5).

    Статусы: active, paid, written_off.
    """

    cooperative_id: UUID
    financial_subject_id: UUID
    accrual_id: UUID
    contribution_type_id: UUID
    original_amount: Money
    paid_amount: Money
    due_date: date | None
    overdue_since: date | None
    status: str = "active"
    created_at: datetime | None = None
    id: UUID | None = None

    @property
    def outstanding_amount(self) -> Money:
        return Money(self.original_amount.amount - self.paid_amount.amount).rounded()

    def apply_payment(self, amount: Money) -> None:
        if self.status != "active":
            return
        self.paid_amount = (self.paid_amount + amount).rounded()
        if self.outstanding_amount.is_zero:
            self.status = "paid"

    def reverse_payment(self, amount: Money) -> None:
        new_paid = self.paid_amount.amount - amount.amount
        if new_paid < Decimal("0"):
            new_paid = Decimal("0")
        self.paid_amount = Money(new_paid).rounded()
        if self.status == "paid" and not self.outstanding_amount.is_zero:
            self.status = "active"

    def mark_written_off(self) -> None:
        self.status = "written_off"

    @classmethod
    def from_accrual_applied(
        cls,
        *,
        cooperative_id: UUID,
        accrual_id: UUID,
        financial_subject_id: UUID,
        contribution_type_id: UUID,
        amount: Decimal,
        due_date: date | None,
        created_at: datetime,
        line_id: UUID,
    ) -> "DebtLine":
        overdue_since: date | None = None
        if due_date is not None and amount > Decimal("0"):
            overdue_since = due_date + timedelta(days=1)
        return cls(
            id=line_id,
            cooperative_id=cooperative_id,
            financial_subject_id=financial_subject_id,
            accrual_id=accrual_id,
            contribution_type_id=contribution_type_id,
            original_amount=Money(amount).rounded(),
            paid_amount=Money.zero(),
            due_date=due_date,
            overdue_since=overdue_since,
            status="active",
            created_at=created_at,
        )


@dataclass
class PenaltySettings:
    """Настройки расчёта пеней для СТ (опционально по виду взноса)."""

    cooperative_id: UUID
    is_enabled: bool
    daily_rate: Decimal
    grace_period_days: int
    effective_from: date
    contribution_type_id: UUID | None = None
    effective_to: date | None = None
    created_at: datetime | None = None
    id: UUID | None = None
