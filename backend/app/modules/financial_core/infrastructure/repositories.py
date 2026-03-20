"""Financial Core repository implementations.

SQLAlchemy implementation of financial core repositories.
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.financial_core.domain.entities import Balance, FinancialSubject
from app.modules.financial_core.domain.repositories import (
    IAccrualAggregateProvider,
    IBalanceRepository,
    IFinancialSubjectRepository,
    IPaymentAggregateProvider,
)
from app.modules.shared.kernel.money import Money

from .models import FinancialSubjectModel


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
