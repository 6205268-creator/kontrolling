"""Financial Core repository implementations.

SQLAlchemy implementation of financial core repositories.
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.financial_core.domain.entities import (
    Balance,
    BalanceSnapshot,
    DebtLine,
    FinancialPeriod,
    FinancialSubject,
    PenaltySettings,
)
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
from app.modules.shared.kernel.money import Money

from .models import (
    BalanceSnapshotModel,
    DebtLineModel,
    FinancialPeriodModel,
    FinancialSubjectModel,
    PenaltySettingsModel,
)


class FinancialSubjectRepository(IFinancialSubjectRepository):
    """SQLAlchemy implementation of FinancialSubject repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> FinancialSubject | None:
        """Get financial subject by ID, filtered by cooperative."""
        query = select(FinancialSubjectModel).where(
            FinancialSubjectModel.id == id,
            FinancialSubjectModel.cooperative_id == cooperative_id,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_all(self, cooperative_id: UUID) -> list[FinancialSubject]:
        """Get all financial subjects for cooperative."""
        query = select(FinancialSubjectModel).where(
            FinancialSubjectModel.cooperative_id == cooperative_id
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def get_by_subject(
        self,
        subject_type: str,
        subject_id: UUID,
        cooperative_id: UUID,
    ) -> FinancialSubject | None:
        """Get financial subject by subject type and ID."""
        query = select(FinancialSubjectModel).where(
            FinancialSubjectModel.subject_type == subject_type,
            FinancialSubjectModel.subject_id == subject_id,
            FinancialSubjectModel.cooperative_id == cooperative_id,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def add(self, entity: FinancialSubject) -> FinancialSubject:
        """Add new financial subject."""
        model = FinancialSubjectModel.from_domain(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def update(self, entity: FinancialSubject) -> FinancialSubject:
        """Update existing financial subject."""
        query = select(FinancialSubjectModel).where(FinancialSubjectModel.id == entity.id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(f"FinancialSubject with id {entity.id} not found")

        model.subject_type = entity.subject_type
        model.subject_id = entity.subject_id
        model.cooperative_id = entity.cooperative_id
        model.code = entity.code
        model.status = entity.status

        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete financial subject by ID."""
        query = select(FinancialSubjectModel).where(
            FinancialSubjectModel.id == id,
            FinancialSubjectModel.cooperative_id == cooperative_id,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.commit()


class BalanceRepository(IBalanceRepository):
    """SQLAlchemy implementation of Balance repository.

    Implements balance calculation as of a specific date (as_of_date).
    Uses IAccrualAggregateProvider and IPaymentAggregateProvider to avoid
    direct dependencies on accruals/payments infrastructure models.

    Rule: Operation participates in balance on date X if and only if:
    1. event_date <= X (accrual_date for Accrual, payment_date for Payment)
    2. date(created_at) <= X
    3. status is correct (applied for Accrual, confirmed for Payment)
    4. NOT cancelled OR (cancelled AND cancelled_at > X)
    """

    def __init__(
        self,
        session: AsyncSession,
        accrual_provider: "IAccrualAggregateProvider",
        payment_provider: "IPaymentAggregateProvider",
    ):
        self.session = session
        self.accrual_provider = accrual_provider
        self.payment_provider = payment_provider

    async def calculate_balance(
        self,
        financial_subject_id: UUID,
        as_of_date: date | None = None,
    ) -> Balance | None:
        """Calculate balance for a financial subject as of a specific date.

        balance = total_accruals (applied) - total_payments (confirmed)

        Args:
            financial_subject_id: ID of financial subject.
            as_of_date: Date to calculate balance for. If None, uses today's date.

        Returns:
            Balance object or None if subject not found.
        """
        # Use today's date if not specified
        if as_of_date is None:
            as_of_date = date.today()

        # Get financial subject
        result = await self.session.execute(
            select(FinancialSubjectModel).where(FinancialSubjectModel.id == financial_subject_id)
        )
        subject = result.scalar_one_or_none()
        if subject is None:
            return None

        # Get aggregated sums from providers
        total_accruals = await self.accrual_provider.sum_participating(
            financial_subject_id=financial_subject_id,
            as_of_date=as_of_date,
        )
        total_payments = await self.payment_provider.sum_participating(
            financial_subject_id=financial_subject_id,
            as_of_date=as_of_date,
        )

        return Balance(
            financial_subject_id=financial_subject_id,
            subject_type=subject.subject_type,
            subject_id=subject.subject_id,
            cooperative_id=subject.cooperative_id,
            code=subject.code,
            total_accruals=Money(total_accruals),
            total_payments=Money(total_payments),
        )

    async def get_balances_by_cooperative(
        self,
        cooperative_id: UUID,
        as_of_date: date | None = None,
    ) -> list[Balance]:
        """Get balances for all financial subjects in cooperative as of a specific date.

        Args:
            cooperative_id: ID of cooperative.
            as_of_date: Date to calculate balances for. If None, uses today's date.

        Returns:
            List of Balance objects.
        """
        # Use today's date if not specified
        if as_of_date is None:
            as_of_date = date.today()

        # Get all financial subjects for cooperative
        result = await self.session.execute(
            select(FinancialSubjectModel).where(
                FinancialSubjectModel.cooperative_id == cooperative_id
            )
        )
        subjects = list(result.scalars().all())

        if not subjects:
            return []

        # Get aggregated sums from providers by cooperative
        accruals_map = await self.accrual_provider.sum_participating_by_cooperative(
            cooperative_id=cooperative_id,
            as_of_date=as_of_date,
        )
        payments_map = await self.payment_provider.sum_participating_by_cooperative(
            cooperative_id=cooperative_id,
            as_of_date=as_of_date,
        )

        # Build result
        balances = []
        for subject in subjects:
            total_accruals = accruals_map.get(subject.id, Decimal("0.00"))
            total_payments = payments_map.get(subject.id, Decimal("0.00"))
            balances.append(
                Balance(
                    financial_subject_id=subject.id,
                    subject_type=subject.subject_type,
                    subject_id=subject.subject_id,
                    cooperative_id=subject.cooperative_id,
                    code=subject.code,
                    total_accruals=Money(total_accruals),
                    total_payments=Money(total_payments),
                )
            )

        return balances


# =============================================================================
# Financial Period Repository
# =============================================================================


class FinancialPeriodRepository(IFinancialPeriodRepository):
    """SQLAlchemy implementation of FinancialPeriod repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> FinancialPeriod | None:
        """Get period by ID, filtered by cooperative."""
        query = select(FinancialPeriodModel).where(
            FinancialPeriodModel.id == id,
            FinancialPeriodModel.cooperative_id == cooperative_id,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_date(self, cooperative_id: UUID, date: date) -> FinancialPeriod | None:
        """Get period that contains the given date."""
        query = select(FinancialPeriodModel).where(
            FinancialPeriodModel.cooperative_id == cooperative_id,
            FinancialPeriodModel.start_date <= date,
            FinancialPeriodModel.end_date >= date,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_all(self, cooperative_id: UUID, year: int | None = None) -> list[FinancialPeriod]:
        """Get all periods for cooperative, optionally filtered by year."""
        query = select(FinancialPeriodModel).where(
            FinancialPeriodModel.cooperative_id == cooperative_id
        )
        if year:
            query = query.where(FinancialPeriodModel.year == year)
        query = query.order_by(
            FinancialPeriodModel.year.desc(),
            FinancialPeriodModel.month.desc(),
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def get_previous_period(self, period: FinancialPeriod) -> FinancialPeriod | None:
        """Get previous period for the same cooperative."""
        from calendar import monthrange

        if period.period_type.value == "monthly":
            # Previous month
            if period.month == 1:
                # Previous year December
                prev_year = period.year - 1
                prev_month = 12
            else:
                prev_year = period.year
                prev_month = period.month - 1

            # Get last day of previous month
            _, last_day = monthrange(prev_year, prev_month)

            query = select(FinancialPeriodModel).where(
                FinancialPeriodModel.cooperative_id == period.cooperative_id,
                FinancialPeriodModel.period_type == "monthly",
                FinancialPeriodModel.year == prev_year,
                FinancialPeriodModel.month == prev_month,
            )
        else:
            # Yearly period - previous year
            prev_year = period.year - 1

            query = select(FinancialPeriodModel).where(
                FinancialPeriodModel.cooperative_id == period.cooperative_id,
                FinancialPeriodModel.period_type == "yearly",
                FinancialPeriodModel.year == prev_year,
            )

        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def add(self, entity: FinancialPeriod) -> FinancialPeriod:
        """Add new period."""
        model = FinancialPeriodModel.from_domain(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def update(self, entity: FinancialPeriod) -> FinancialPeriod:
        """Update existing period."""
        query = select(FinancialPeriodModel).where(FinancialPeriodModel.id == entity.id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(f"FinancialPeriod with id {entity.id} not found")

        model.status = entity.status
        model.closed_at = entity.closed_at
        model.closed_by_user_id = entity.closed_by_user_id

        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete period by ID."""
        query = select(FinancialPeriodModel).where(
            FinancialPeriodModel.id == id,
            FinancialPeriodModel.cooperative_id == cooperative_id,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.commit()


# =============================================================================
# Balance Snapshot Repository
# =============================================================================


class BalanceSnapshotRepository(IBalanceSnapshotRepository):
    """SQLAlchemy implementation of BalanceSnapshot repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_financial_subject(
        self,
        financial_subject_id: UUID,
        period_id: UUID,
    ) -> BalanceSnapshot | None:
        """Get snapshot for financial subject and period."""
        query = select(BalanceSnapshotModel).where(
            BalanceSnapshotModel.financial_subject_id == financial_subject_id,
            BalanceSnapshotModel.period_id == period_id,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_cooperative(
        self,
        cooperative_id: UUID,
        period_id: UUID,
    ) -> list[BalanceSnapshot]:
        """Get all snapshots for cooperative and period."""
        query = select(BalanceSnapshotModel).where(
            BalanceSnapshotModel.cooperative_id == cooperative_id,
            BalanceSnapshotModel.period_id == period_id,
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def add(self, entity: BalanceSnapshot) -> BalanceSnapshot:
        """Add new snapshot."""
        model = BalanceSnapshotModel.from_domain(entity)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        await self.session.commit()
        return model.to_domain()

    async def delete_by_period(
        self,
        period_id: UUID,
        cooperative_id: UUID,
    ) -> int:
        """Delete all snapshots for period. Returns count of deleted."""
        query = select(BalanceSnapshotModel).where(
            BalanceSnapshotModel.period_id == period_id,
            BalanceSnapshotModel.cooperative_id == cooperative_id,
        )
        result = await self.session.execute(query)
        models = result.scalars().all()

        count = 0
        for model in models:
            await self.session.delete(model)
            count += 1

        if count > 0:
            await self.session.commit()

        return count


class DebtLineRepository(IDebtLineRepository):
    """SQLAlchemy-реализация репозитория строк долга."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, line_id: UUID, cooperative_id: UUID) -> DebtLine | None:
        q = select(DebtLineModel).where(
            DebtLineModel.id == line_id,
            DebtLineModel.cooperative_id == cooperative_id,
        )
        r = await self.session.execute(q)
        m = r.scalar_one_or_none()
        return m.to_domain() if m else None

    async def get_by_accrual_id(self, accrual_id: UUID) -> DebtLine | None:
        q = select(DebtLineModel).where(DebtLineModel.accrual_id == accrual_id)
        r = await self.session.execute(q)
        m = r.scalar_one_or_none()
        return m.to_domain() if m else None

    async def get_by_financial_subject(
        self,
        financial_subject_id: UUID,
        cooperative_id: UUID,
    ) -> list[DebtLine]:
        q = select(DebtLineModel).where(
            DebtLineModel.financial_subject_id == financial_subject_id,
            DebtLineModel.cooperative_id == cooperative_id,
        )
        r = await self.session.execute(q)
        return [row.to_domain() for row in r.scalars().all()]

    async def get_active_with_outstanding(self, cooperative_id: UUID) -> list[DebtLine]:
        from sqlalchemy import and_

        q = select(DebtLineModel).where(
            and_(
                DebtLineModel.cooperative_id == cooperative_id,
                DebtLineModel.status == "active",
            )
        )
        r = await self.session.execute(q)
        lines = [row.to_domain() for row in r.scalars().all()]
        return [ln for ln in lines if ln.outstanding_amount.is_positive]

    async def get_overdue(self, cooperative_id: UUID, as_of_date: date) -> list[DebtLine]:
        from sqlalchemy import and_

        q = select(DebtLineModel).where(
            and_(
                DebtLineModel.cooperative_id == cooperative_id,
                DebtLineModel.status == "active",
                DebtLineModel.overdue_since.is_not(None),
                DebtLineModel.overdue_since <= as_of_date,
            )
        )
        r = await self.session.execute(q)
        lines = [row.to_domain() for row in r.scalars().all()]
        return [ln for ln in lines if ln.outstanding_amount.is_positive]

    async def add(self, entity: DebtLine) -> DebtLine:
        m = DebtLineModel.from_domain(entity)
        self.session.add(m)
        await self.session.commit()
        await self.session.refresh(m)
        return m.to_domain()

    async def update(self, entity: DebtLine) -> DebtLine:
        q = select(DebtLineModel).where(DebtLineModel.id == entity.id)
        r = await self.session.execute(q)
        m = r.scalar_one_or_none()
        if m is None:
            raise ValueError(f"DebtLine {entity.id} not found")
        m.paid_amount = entity.paid_amount.amount
        m.status = entity.status
        await self.session.commit()
        await self.session.refresh(m)
        return m.to_domain()


class PenaltySettingsRepository(IPenaltySettingsRepository):
    """SQLAlchemy-реализация настроек пеней."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_cooperative(self, cooperative_id: UUID) -> list[PenaltySettings]:
        q = (
            select(PenaltySettingsModel)
            .where(PenaltySettingsModel.cooperative_id == cooperative_id)
            .order_by(PenaltySettingsModel.effective_from.desc())
        )
        r = await self.session.execute(q)
        return [row.to_domain() for row in r.scalars().all()]

    async def get_by_id(self, settings_id: UUID, cooperative_id: UUID) -> PenaltySettings | None:
        q = select(PenaltySettingsModel).where(
            PenaltySettingsModel.id == settings_id,
            PenaltySettingsModel.cooperative_id == cooperative_id,
        )
        r = await self.session.execute(q)
        m = r.scalar_one_or_none()
        return m.to_domain() if m else None

    async def add(self, entity: PenaltySettings) -> PenaltySettings:
        m = PenaltySettingsModel.from_domain(entity)
        self.session.add(m)
        await self.session.commit()
        await self.session.refresh(m)
        return m.to_domain()

    async def update(self, entity: PenaltySettings) -> PenaltySettings:
        q = select(PenaltySettingsModel).where(PenaltySettingsModel.id == entity.id)
        r = await self.session.execute(q)
        m = r.scalar_one_or_none()
        if m is None:
            raise ValueError(f"PenaltySettings {entity.id} not found")
        m.contribution_type_id = entity.contribution_type_id
        m.is_enabled = entity.is_enabled
        m.daily_rate = entity.daily_rate
        m.grace_period_days = entity.grace_period_days
        m.effective_from = entity.effective_from
        m.effective_to = entity.effective_to
        await self.session.commit()
        await self.session.refresh(m)
        return m.to_domain()

    async def delete(self, settings_id: UUID, cooperative_id: UUID) -> None:
        q = select(PenaltySettingsModel).where(
            PenaltySettingsModel.id == settings_id,
            PenaltySettingsModel.cooperative_id == cooperative_id,
        )
        r = await self.session.execute(q)
        m = r.scalar_one_or_none()
        if m:
            await self.session.delete(m)
            await self.session.commit()
