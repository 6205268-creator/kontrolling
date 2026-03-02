"""Accruals repository implementations.

SQLAlchemy implementation of accruals repositories.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.accruals.domain.entities import Accrual, ContributionType
from app.modules.accruals.domain.repositories import IAccrualRepository, IContributionTypeRepository

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
            .join(FinancialSubjectModel, AccrualModel.financial_subject_id == FinancialSubjectModel.id)
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
            .join(FinancialSubjectModel, AccrualModel.financial_subject_id == FinancialSubjectModel.id)
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
            .join(FinancialSubjectModel, AccrualModel.financial_subject_id == FinancialSubjectModel.id)
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
        """Update existing accrual."""
        query = select(AccrualModel).where(AccrualModel.id == entity.id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if model is None:
            raise ValueError(f"Accrual with id {entity.id} not found")

        model.financial_subject_id = entity.financial_subject_id
        model.contribution_type_id = entity.contribution_type_id
        model.amount = entity.amount
        model.accrual_date = entity.accrual_date
        model.period_start = entity.period_start
        model.period_end = entity.period_end
        model.status = entity.status
        
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete accrual by ID."""
        from app.modules.financial_core.infrastructure.models import FinancialSubjectModel
        
        query = (
            select(AccrualModel)
            .join(FinancialSubjectModel, AccrualModel.financial_subject_id == FinancialSubjectModel.id)
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
