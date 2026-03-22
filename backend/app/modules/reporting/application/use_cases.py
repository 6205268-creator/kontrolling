"""Use cases for reporting module."""

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from app.modules.financial_core.domain.entities import FinancialPeriod, PeriodType
from app.modules.financial_core.domain.penalty_strategy import PenaltyCalculator
from app.modules.financial_core.domain.repositories import (
    IAccrualAggregateProvider,
    IBalanceRepository,
    IBalanceSnapshotRepository,
    IDebtLineRepository,
    IFinancialPeriodRepository,
    IFinancialSubjectRepository,
    IPaymentAggregateProvider,
    IPenaltySettingsRepository,
)


@dataclass(frozen=True)
class TurnoverSheetRow:
    """Строка оборотной ведомости по одному финансовому субъекту."""

    financial_subject_id: UUID
    code: str
    opening_balance: Decimal
    accrued_in_period: Decimal
    paid_in_period: Decimal
    closing_balance: Decimal


class GetTurnoverSheetUseCase:
    """Оборотная ведомость за календарный месяц (при наличии — границы из FinancialPeriod)."""

    def __init__(
        self,
        fs_repo: IFinancialSubjectRepository,
        period_repo: IFinancialPeriodRepository,
        snapshot_repo: IBalanceSnapshotRepository,
        balance_repo: IBalanceRepository,
        accrual_provider: IAccrualAggregateProvider,
        payment_provider: IPaymentAggregateProvider,
    ):
        self._fs_repo = fs_repo
        self._period_repo = period_repo
        self._snapshot_repo = snapshot_repo
        self._balance_repo = balance_repo
        self._accrual_provider = accrual_provider
        self._payment_provider = payment_provider

    @staticmethod
    def _calendar_month_bounds(year: int, month: int) -> tuple[date, date]:
        last = monthrange(year, month)[1]
        return date(year, month, 1), date(year, month, last)

    async def _resolve_period_bounds(
        self,
        cooperative_id: UUID,
        year: int,
        month: int,
    ) -> tuple[date, date, FinancialPeriod | None]:
        periods = await self._period_repo.get_all(cooperative_id, year)
        period = next(
            (p for p in periods if p.period_type == PeriodType.MONTHLY and p.month == month),
            None,
        )
        if period:
            return period.start_date, period.end_date, period
        start, end = self._calendar_month_bounds(year, month)
        return start, end, None

    async def _opening_balance(
        self,
        financial_subject_id: UUID,
        cooperative_id: UUID,
        period_entity: FinancialPeriod | None,
        p_start: date,
    ) -> Decimal:
        prev_period = None
        if period_entity is not None:
            prev_period = await self._period_repo.get_previous_period(period_entity)
        if prev_period is None:
            day_before = p_start - timedelta(days=1)
            prev_period = await self._period_repo.get_by_date(cooperative_id, day_before)

        if prev_period is not None and prev_period.status in ("closed", "locked"):
            snap = await self._snapshot_repo.get_by_financial_subject(
                financial_subject_id,
                prev_period.id,
            )
            if snap is not None:
                return snap.balance.amount

        ref_date = p_start - timedelta(days=1)
        bal = await self._balance_repo.calculate_balance(financial_subject_id, ref_date)
        return bal.balance.amount if bal else Decimal("0.00")

    async def execute(self, cooperative_id: UUID, year: int, month: int) -> list[TurnoverSheetRow]:
        p_start, p_end, period_entity = await self._resolve_period_bounds(
            cooperative_id, year, month
        )
        subjects = await self._fs_repo.get_all(cooperative_id)
        rows: list[TurnoverSheetRow] = []

        for sub in subjects:
            opening = await self._opening_balance(sub.id, cooperative_id, period_entity, p_start)
            accrued = await self._accrual_provider.sum_applied_in_period(sub.id, p_start, p_end)
            paid = await self._payment_provider.sum_confirmed_in_period(sub.id, p_start, p_end)
            closing = opening + accrued - paid
            rows.append(
                TurnoverSheetRow(
                    financial_subject_id=sub.id,
                    code=sub.code,
                    opening_balance=opening,
                    accrued_in_period=accrued,
                    paid_in_period=paid,
                    closing_balance=closing,
                )
            )

        return rows


class GenerateDebtorReportUseCase:
    """Отчёт по должникам: активные DebtLine и расчётные пени на дату."""

    def __init__(
        self,
        read_service,
        debt_line_repo: IDebtLineRepository,
        penalty_settings_repo: IPenaltySettingsRepository,
        penalty_calculator: PenaltyCalculator,
    ):
        self.read_service = read_service
        self.debt_line_repo = debt_line_repo
        self.penalty_settings_repo = penalty_settings_repo
        self.penalty_calculator = penalty_calculator

    async def execute(
        self,
        cooperative_id: UUID,
        as_of_date: date,
        min_debt: Decimal = Decimal("0.00"),
    ):
        """Сводка по должникам с пенями; при отсутствии строк долга — пустой список."""
        rows = await self.read_service.get_debtors_with_penalties(
            cooperative_id,
            as_of_date,
            min_debt,
            self.debt_line_repo,
            self.penalty_settings_repo,
            self.penalty_calculator,
        )
        if rows:
            return rows
        return await self.read_service.get_debtors_report(cooperative_id, min_debt)


class GenerateCashFlowUseCase:
    """Use case for generating cash flow report."""

    def __init__(self, read_service):
        self.read_service = read_service

    async def execute(self, cooperative_id: UUID, period_start: date, period_end: date):
        """Generate cash flow report for period."""
        return await self.read_service.get_cash_flow_report(
            cooperative_id, period_start, period_end
        )
