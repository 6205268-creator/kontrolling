"""Cooperative repository implementation.

SQLAlchemy implementation of ICooperativeRepository.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cooperative_core.domain.entities import Cooperative
from app.modules.cooperative_core.domain.repositories import ICooperativeRepository

from .mappers import domain_to_orm, orm_to_domain
from .models import CooperativeModel


class CooperativeRepository(ICooperativeRepository):
    """SQLAlchemy implementation of Cooperative repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID, cooperative_id: UUID | None) -> Cooperative | None:
        """Get cooperative by ID. If cooperative_id is None (admin), return by id only."""
        query = select(CooperativeModel).where(CooperativeModel.id == id)
        if cooperative_id is not None:
            query = query.where(CooperativeModel.id == cooperative_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return orm_to_domain(model) if model else None

    async def get_all(self, cooperative_id: UUID) -> list[Cooperative]:
        """Get all cooperatives for given cooperative_id."""
        query = select(CooperativeModel).where(CooperativeModel.id == cooperative_id)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [orm_to_domain(m) for m in models]

    async def get_all_for_admin(self) -> list[Cooperative]:
        """Get all cooperatives (admin only)."""
        query = select(CooperativeModel)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [orm_to_domain(m) for m in models]

    async def add(self, entity: Cooperative) -> Cooperative:
        """Add new cooperative."""
        model = domain_to_orm(entity)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return orm_to_domain(model)

    async def update(self, entity: Cooperative) -> Cooperative:
        """Update existing cooperative."""
        query = select(CooperativeModel).where(CooperativeModel.id == entity.id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(f"Cooperative with id {entity.id} not found")

        model.name = entity.name
        model.unp = entity.unp
        model.address = entity.address
        model.period_reopen_allowed_days = entity.period_reopen_allowed_days
        model.penalty_accrual_schedule = entity.penalty_accrual_schedule

        await self.session.flush()
        await self.session.refresh(model)
        return orm_to_domain(model)

    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete cooperative by ID."""
        query = select(CooperativeModel).where(
            CooperativeModel.id == id,
            CooperativeModel.id == cooperative_id,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.flush()
