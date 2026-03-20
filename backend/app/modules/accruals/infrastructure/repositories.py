"""Accruals repository implementations.

SQLAlchemy implementation of accruals repositories.
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.accruals.domain.entities import Accrual, ContributionType
from app.modules.accruals.domain.repositories import IAccrualRepository, IContributionTypeRepository
from app.modules.financial_core.domain.repositories import IAccrualAggregateProvider

from .models import AccrualModel, ContributionTypeModel


class AccrualRepository(IAccrualRepository):
    """SQLAlchemy implementation of Accrual repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> Accrual | None:
        """Get accrual by ID, filtered by cooperative via financial_subject."""
        from app.modules.financial_core.infrastructure.models import FinancialSubjectModel

        query = (
            select(AccrualModel)
            .join(
                FinancialSubjectModel, AccrualModel.financial_subject_id == FinancialSubjectModel.id
            )
            .where(
                AccrualModel.id == id,
                FinancialSubjectModel.cooperative_id == cooperative_id,
            )
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_financial_subject(
        self,
        financial_subject_id: UUID,
        cooperative_id: UUID,
    ) -> list[Accrual]:
        """Get all accruals for a financial subject."""
        from app.modules.financial_core.infrastructure.models import FinancialSubjectModel

        query = (
            select(AccrualModel)
            .join(
                FinancialSubjectModel, AccrualModel.financial_subject_id == FinancialSubjectModel.id
            )
            .where(
                AccrualModel.financial_subject_id == financial_subject_id,
                FinancialSubjectModel.cooperative_id == cooperative_id,
            )
            .order_by(AccrualModel.accrual_date.desc())
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def get_by_cooperative(self, cooperative_id: UUID) -> list[Accrual]:
        """Get all accruals for a cooperative."""
        from app.modules.financial_core.infrastructure.models import FinancialSubjectModel

        query = (
            select(AccrualModel)
            .join(
                FinancialSubjectModel, AccrualModel.financial_subject_id == FinancialSubjectModel.id
            )
            .where(FinancialSubjectModel.cooperative_id == cooperative_id)
            .order_by(AccrualModel.accrual_date.desc())
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def get_all(self, cooperative_id: UUID) -> list[Accrual]:
        """Get all accruals for a cooperative (alias for get_by_cooperative)."""
        return await self.get_by_cooperative(cooperative_id)

    async def add(self, entity: Accrual) -> Accrual:
        """Add new accrual."""
        model = AccrualModel.from_domain(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def update(self, entity: Accrual) -> Accrual:
        """Update existing accrual.

        Note: amount is immutable - not updated to preserve financial integrity.
        """
        query = select(AccrualModel).where(AccrualModel.id == entity.id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(f"Accrual with id {entity.id} not found")

        model.financial_subject_id = entity.financial_subject_id
        model.contribution_type_id = entity.contribution_type_id
        # amount is immutable - not updated
        model.accrual_date = entity.accrual_date
        model.period_start = entity.period_start
        model.period_end = entity.period_end
        model.status = entity.status
        model.cancelled_at = entity.cancelled_at
        model.cancelled_by_user_id = entity.cancelled_by_user_id
        model.cancellation_reason = entity.cancellation_reason

        await self.session.commit()

        # Re-fetch to get fresh data from DB (amount should be unchanged)
        self.session.expunge(model)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain()

    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete accrual by ID."""
        from app.modules.financial_core.infrastructure.models import FinancialSubjectModel

        query = (
            select(AccrualModel)
            .join(
                FinancialSubjectModel, AccrualModel.financial_subject_id == FinancialSubjectModel.id
            )
            .where(
                AccrualModel.id == id,
                FinancialSubjectModel.cooperative_id == cooperative_id,
            )
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.commit()


class ContributionTypeRepository(IContributionTypeRepository):
    """SQLAlchemy implementation of ContributionType repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> ContributionType | None:
        """Get contribution type by ID. Note: cooperative_id not used."""
        query = select(ContributionTypeModel).where(ContributionTypeModel.id == id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_all(self, cooperative_id: UUID) -> list[ContributionType]:
        """Get all contribution types. Note: cooperative_id not used."""
        query = select(ContributionTypeModel).order_by(ContributionTypeModel.name)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def get_by_code(self, code: str) -> ContributionType | None:
        """Get contribution type by code."""
        query = select(ContributionTypeModel).where(ContributionTypeModel.code == code)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def add(self, entity: ContributionType) -> ContributionType:
        """Add new contribution type."""
        model = ContributionTypeModel.from_domain(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def update(self, entity: ContributionType) -> ContributionType:
        """Update existing contribution type."""
        query = select(ContributionTypeModel).where(ContributionTypeModel.id == entity.id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(f"ContributionType with id {entity.id} not found")

        model.name = entity.name
        model.code = entity.code
        model.description = entity.description

        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete contribution type by ID."""
        query = select(ContributionTypeModel).where(ContributionTypeModel.id == id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.commit()


class AccrualAggregateProvider(IAccrualAggregateProvider):
    """Accrual aggregate provider for balance calculation.

    This class provides aggregated accrual data to financial_core module
    without requiring direct dependency on AccrualModel.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def sum_participating(
        self,
        financial_subject_id: UUID,
        as_of_date: date,
    ) -> Decimal:
        """Get sum of accruals participating in balance as of date.

        Uses BalanceParticipationSqlFilter to determine which accruals participate.
        """
        from app.modules.financial_core.domain.balance_spec import BalanceParticipationRule
        from app.modules.financial_core.infrastructure.balance_spec_sql import (
            BalanceParticipationSqlFilter,
        )

        rule = BalanceParticipationRule(as_of_date)
        sql_filter = BalanceParticipationSqlFilter(rule)

        filter_condition = sql_filter.accrual_filter(
            AccrualModel,
            financial_subject_id_filter=financial_subject_id,
        )

        result = await self.session.execute(
            select(func.sum(AccrualModel.amount)).where(filter_condition)
        )
        total = result.scalar() or Decimal("0.00")
        return total

    async def sum_participating_by_cooperative(
        self,
        cooperative_id: UUID,
        as_of_date: date,
    ) -> dict[UUID, Decimal]:
        """Get sums of accruals for all subjects in cooperative as of date.

        Returns dict mapping financial_subject_id to sum.
        """
        from app.modules.financial_core.domain.balance_spec import BalanceParticipationRule
        from app.modules.financial_core.infrastructure.balance_spec_sql import (
            BalanceParticipationSqlFilter,
        )
        from app.modules.financial_core.infrastructure.models import FinancialSubjectModel

        rule = BalanceParticipationRule(as_of_date)
        sql_filter = BalanceParticipationSqlFilter(rule)

        # Join with FinancialSubject to filter by cooperative
        filter_condition = sql_filter.accrual_filter(AccrualModel)
        filter_condition = filter_condition & (
            FinancialSubjectModel.cooperative_id == cooperative_id
        )

        result = await self.session.execute(
            select(
                AccrualModel.financial_subject_id,
                func.sum(AccrualModel.amount).label("total"),
            )
            .join(
                FinancialSubjectModel,
                AccrualModel.financial_subject_id == FinancialSubjectModel.id,
            )
            .where(filter_condition)
            .group_by(AccrualModel.financial_subject_id)
        )

        return {row[0]: (row[1] or Decimal("0.00")) for row in result.all()}
