"""Стратегии расчёта пеней (изолированы для смены формулы)."""

from abc import ABC, abstractmethod
from datetime import date, timedelta

from app.modules.shared.kernel.money import Money

from .entities import DebtLine, PenaltySettings


class IPenaltyStrategy(ABC):
    """Интерфейс стратегии расчёта суммы пени."""

    @abstractmethod
    def calculate(
        self,
        outstanding_amount: Money,
        overdue_days: int,
        settings: PenaltySettings,
    ) -> Money:
        """Вернуть сумму пени (округление — на усмотрение реализации)."""
        ...


class SimpleDailyPenaltyStrategy(IPenaltyStrategy):
    """Простые проценты: остаток × дневная ставка × дни просрочки."""

    def calculate(
        self,
        outstanding_amount: Money,
        overdue_days: int,
        settings: PenaltySettings,
    ) -> Money:
        if overdue_days <= 0:
            return Money.zero()
        penalty = outstanding_amount.amount * settings.daily_rate * overdue_days
        return Money(penalty).rounded()


class PenaltyCalculator:
    """Доменный сервис: дата отсечения, дни просрочки, делегирование стратегии."""

    def __init__(self, strategy: IPenaltyStrategy):
        self._strategy = strategy

    def calculate(
        self,
        debt_line: DebtLine,
        settings: PenaltySettings,
        as_of_date: date,
    ) -> Money:
        if not settings.is_enabled:
            return Money.zero()
        if debt_line.status != "active":
            return Money.zero()
        if debt_line.due_date is None:
            return Money.zero()
        if debt_line.outstanding_amount.is_zero:
            return Money.zero()

        penalty_start = debt_line.due_date + timedelta(days=settings.grace_period_days + 1)
        if as_of_date < penalty_start:
            return Money.zero()

        overdue_days = (as_of_date - penalty_start).days + 1
        return self._strategy.calculate(
            debt_line.outstanding_amount,
            overdue_days,
            settings,
        )
