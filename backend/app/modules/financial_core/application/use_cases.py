"""Use cases for financial_core module."""

from datetime import UTC, date, datetime
from uuid import UUID

from app.modules.cooperative_core.domain.repositories import ICooperativeRepository

from ..domain.entities import Balance, BalanceSnapshot, FinancialPeriod, FinancialSubject
from ..domain.repositories import (
    IBalanceRepository,
    IBalanceSnapshotRepository,
    IFinancialPeriodRepository,
    IFinancialSubjectRepository,
)
from .dtos import FinancialSubjectCreate
from .period_auto_lock import apply_auto_lock_if_window_expired, ensure_aware_utc


async def _balance_with_snapshot_if_closed(
    balance_repo: IBalanceRepository,
    period_repo: IFinancialPeriodRepository,
    snapshot_repo: IBalanceSnapshotRepository,
    financial_subject_id: UUID,
    as_of_date: date,
) -> Balance | None:
    """Баланс на дату; для закрытого/заблокированного периода — из снимка, если есть."""
    bal = await balance_repo.calculate_balance(financial_subject_id, as_of_date)
    if bal is None:
        return None
    period = await period_repo.get_by_date(bal.cooperative_id, as_of_date)
    if period and period.status in ("closed", "locked") and period.id:
        snap = await snapshot_repo.get_by_financial_subject(financial_subject_id, period.id)
        if snap is not None:
            return Balance(
                financial_subject_id=bal.financial_subject_id,
                subject_type=bal.subject_type,
                subject_id=bal.subject_id,
                cooperative_id=bal.cooperative_id,
                code=bal.code,
                total_accruals=snap.total_accruals,
                total_payments=snap.total_payments,
            )
    return bal


class CreateFinancialSubjectUseCase:
    """Use case for creating a FinancialSubject.

    Typically called by event handler when LandPlot or Meter is created.
    """

    def __init__(self, repo: IFinancialSubjectRepository):
        self.repo = repo

    async def execute(self, data: FinancialSubjectCreate) -> FinancialSubject:
        """Create a new financial subject."""
        entity = FinancialSubject(
            id=UUID(int=0),  # Will be set by repository
            subject_type=data.subject_type,
            subject_id=data.subject_id,
            cooperative_id=data.cooperative_id,
            code=data.code,
            status=data.status,
        )

        return await self.repo.add(entity)


class GetFinancialSubjectUseCase:
    """Use case for getting a FinancialSubject by ID."""

    def __init__(self, repo: IFinancialSubjectRepository):
        self.repo = repo

    async def execute(self, subject_id: UUID, cooperative_id: UUID) -> FinancialSubject | None:
        """Get financial subject by ID."""
        return await self.repo.get_by_id(subject_id, cooperative_id)


class GetFinancialSubjectsUseCase:
    """Use case for getting list of FinancialSubjects."""

    def __init__(self, repo: IFinancialSubjectRepository):
        self.repo = repo

    async def execute(self, cooperative_id: UUID) -> list[FinancialSubject]:
        """Get all financial subjects for cooperative."""
        return await self.repo.get_all(cooperative_id)


class GetBalanceUseCase:
    """Use case for getting balance of a FinancialSubject as of a specific date."""

    def __init__(
        self,
        balance_repo: IBalanceRepository,
        period_repo: IFinancialPeriodRepository,
        snapshot_repo: IBalanceSnapshotRepository,
    ):
        self.balance_repo = balance_repo
        self.period_repo = period_repo
        self.snapshot_repo = snapshot_repo

    async def execute(
        self,
        financial_subject_id: UUID,
        as_of_date: date | None = None,
    ) -> Balance | None:
        """Get balance for financial subject as of a specific date.

        Args:
            financial_subject_id: ID of financial subject.
            as_of_date: Date to calculate balance for. If None, uses today's date.
        """
        as_of = as_of_date or date.today()
        return await _balance_with_snapshot_if_closed(
            self.balance_repo,
            self.period_repo,
            self.snapshot_repo,
            financial_subject_id,
            as_of,
        )


class GetBalancesByCooperativeUseCase:
    """Use case for getting balances of all FinancialSubjects in cooperative as of a specific date."""

    def __init__(
        self,
        balance_repo: IBalanceRepository,
        period_repo: IFinancialPeriodRepository,
        snapshot_repo: IBalanceSnapshotRepository,
        fs_repo: IFinancialSubjectRepository,
    ):
        self.balance_repo = balance_repo
        self.period_repo = period_repo
        self.snapshot_repo = snapshot_repo
        self.fs_repo = fs_repo

    async def execute(
        self,
        cooperative_id: UUID,
        as_of_date: date | None = None,
    ) -> list[Balance]:
        """Get balances for all financial subjects in cooperative as of a specific date.

        Args:
            cooperative_id: ID of cooperative.
            as_of_date: Date to calculate balances for. If None, uses today's date.
        """
        as_of = as_of_date or date.today()
        subjects = await self.fs_repo.get_all(cooperative_id)
        out: list[Balance] = []
        for sub in subjects:
            bal = await _balance_with_snapshot_if_closed(
                self.balance_repo,
                self.period_repo,
                self.snapshot_repo,
                sub.id,
                as_of,
            )
            if bal is not None:
                out.append(bal)
        return out


# =============================================================================
# Financial Period Use Cases
# =============================================================================


class CreateFinancialPeriodUseCase:
    """Use case for creating a financial period."""

    def __init__(self, period_repo: IFinancialPeriodRepository):
        self.period_repo = period_repo

    async def execute(
        self,
        cooperative_id: UUID,
        period_type: str,
        year: int,
        month: int | None = None,
    ) -> FinancialPeriod:
        """Create a new financial period.

        Args:
            cooperative_id: ID of cooperative.
            period_type: 'monthly' or 'yearly'.
            year: Year.
            month: Month (1-12) for monthly periods, None for yearly.
        """
        if period_type == "monthly":
            period = FinancialPeriod.create_monthly(cooperative_id, year, month)
        else:
            period = FinancialPeriod.create_yearly(cooperative_id, year)

        return await self.period_repo.add(period)


class CloseFinancialPeriodUseCase:
    """Use case for closing a financial period."""

    def __init__(
        self,
        period_repo: IFinancialPeriodRepository,
        balance_repo: IBalanceRepository,
        snapshot_repo: IBalanceSnapshotRepository,
        fs_repo: IFinancialSubjectRepository,
    ):
        self.period_repo = period_repo
        self.balance_repo = balance_repo
        self.snapshot_repo = snapshot_repo
        self.fs_repo = fs_repo

    async def execute(
        self,
        period_id: UUID,
        cooperative_id: UUID,
        user_id: UUID,
        now: datetime,
    ) -> FinancialPeriod:
        """Close a financial period.

        Args:
            period_id: ID of period to close.
            cooperative_id: ID of cooperative (for authorization).
            user_id: ID of user closing the period.
            now: Current datetime.
        """
        period = await self.period_repo.get_by_id(period_id, cooperative_id)
        if not period:
            raise ValueError(f"Period {period_id} not found")

        prev = await self.period_repo.get_previous_period(period)
        if prev is not None and prev.status == "open":
            raise ValueError("Нельзя закрыть период, пока не закрыт предыдущий")

        period.close(user_id, now)
        updated = await self.period_repo.update(period)

        subjects = await self.fs_repo.get_all(cooperative_id)
        for sub in subjects:
            bal = await self.balance_repo.calculate_balance(sub.id, updated.end_date)
            if bal is None:
                continue
            snap = BalanceSnapshot(
                financial_subject_id=sub.id,
                period_id=updated.id,
                cooperative_id=cooperative_id,
                total_accruals=bal.total_accruals,
                total_payments=bal.total_payments,
            )
            await self.snapshot_repo.add(snap)

        return updated


class ReopenFinancialPeriodUseCase:
    """Use case for reopening a closed/locked financial period."""

    def __init__(
        self,
        period_repo: IFinancialPeriodRepository,
        snapshot_repo: IBalanceSnapshotRepository,
        coop_repo: ICooperativeRepository,
    ):
        self.period_repo = period_repo
        self.snapshot_repo = snapshot_repo
        self.coop_repo = coop_repo

    async def execute(
        self,
        period_id: UUID,
        cooperative_id: UUID,
        user_id: UUID,
        now: datetime,
        is_admin: bool = False,
        period_reopen_allowed_days: int = 30,
    ) -> FinancialPeriod:
        """Reopen a financial period.

        Args:
            period_id: ID of period to reopen.
            cooperative_id: ID of cooperative.
            user_id: ID of user reopening the period.
            now: Current datetime.
            is_admin: True if user is admin (can reopen anytime).
            period_reopen_allowed_days: Days allowed for treasurer to reopen.
        """
        period = await self.period_repo.get_by_id(period_id, cooperative_id)
        if not period:
            raise ValueError(f"Period {period_id} not found")

        coop = await self.coop_repo.get_by_id(
            cooperative_id,
            None if is_admin else cooperative_id,
        )
        allowed = coop.period_reopen_allowed_days if coop else period_reopen_allowed_days
        if apply_auto_lock_if_window_expired(period, allowed, now):
            await self.period_repo.update(period)

        if not is_admin and period.status == "locked":
            raise ValueError("Только администратор может переоткрыть заблокированный период")

        if not is_admin and period.status == "closed":
            if period.closed_at:
                days_since_close = (
                    ensure_aware_utc(now) - ensure_aware_utc(period.closed_at)
                ).days
                if days_since_close > allowed:
                    raise ValueError(
                        f"Cannot reopen period: more than {allowed} days since close"
                    )

        await self.snapshot_repo.delete_by_period(period_id, cooperative_id)

        period.reopen(now)
        return await self.period_repo.update(period)


class LockFinancialPeriodUseCase:
    """Use case for locking a financial period."""

    def __init__(self, period_repo: IFinancialPeriodRepository):
        self.period_repo = period_repo

    async def execute(
        self,
        period_id: UUID,
        cooperative_id: UUID,
    ) -> FinancialPeriod:
        """Lock a financial period (admin only).

        Args:
            period_id: ID of period to lock.
            cooperative_id: ID of cooperative.
        """
        period = await self.period_repo.get_by_id(period_id, cooperative_id)
        if not period:
            raise ValueError(f"Period {period_id} not found")

        period.lock()
        return await self.period_repo.update(period)


class GetFinancialPeriodsUseCase:
    """Use case for getting financial periods."""

    def __init__(
        self,
        period_repo: IFinancialPeriodRepository,
        coop_repo: ICooperativeRepository,
    ):
        self.period_repo = period_repo
        self.coop_repo = coop_repo

    async def execute(
        self,
        cooperative_id: UUID,
        year: int | None = None,
    ) -> list[FinancialPeriod]:
        """Get financial periods for cooperative.

        Args:
            cooperative_id: ID of cooperative.
            year: Optional year filter.
        """
        periods = await self.period_repo.get_all(cooperative_id, year)
        coop = await self.coop_repo.get_by_id(cooperative_id, cooperative_id)
        allowed = coop.period_reopen_allowed_days if coop else 30
        now = datetime.now(UTC)
        for p in periods:
            if apply_auto_lock_if_window_expired(p, allowed, now):
                await self.period_repo.update(p)
        return periods


class GetFinancialPeriodByDateUseCase:
    """Use case for getting financial period by date."""

    def __init__(
        self,
        period_repo: IFinancialPeriodRepository,
        coop_repo: ICooperativeRepository,
    ):
        self.period_repo = period_repo
        self.coop_repo = coop_repo

    async def execute(
        self,
        cooperative_id: UUID,
        date: date,
    ) -> FinancialPeriod | None:
        """Get financial period that contains the given date.

        Args:
            cooperative_id: ID of cooperative.
            date: Date to find period for.
        """
        period = await self.period_repo.get_by_date(cooperative_id, date)
        if period is None:
            return None
        coop = await self.coop_repo.get_by_id(cooperative_id, cooperative_id)
        allowed = coop.period_reopen_allowed_days if coop else 30
        now = datetime.now(UTC)
        if apply_auto_lock_if_window_expired(period, allowed, now):
            await self.period_repo.update(period)
        return period
