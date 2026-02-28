"""Land Management repository implementations.

SQLAlchemy implementation of land management repositories.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.land_management.domain.entities import LandPlot, Owner, PlotOwnership
from app.modules.land_management.domain.repositories import (
    ILandPlotRepository,
    IOwnerRepository,
    IPlotOwnershipRepository,
)

from .models import LandPlotModel, OwnerModel, PlotOwnershipModel


class LandPlotRepository(ILandPlotRepository):
    """SQLAlchemy implementation of LandPlot repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> LandPlot | None:
        """Get land plot by ID, filtered by cooperative."""
        query = select(LandPlotModel).where(
            LandPlotModel.id == id,
            LandPlotModel.cooperative_id == cooperative_id,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_all(self, cooperative_id: UUID) -> list[LandPlot]:
        """Get all land plots for cooperative."""
        query = select(LandPlotModel).where(LandPlotModel.cooperative_id == cooperative_id)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def get_by_plot_number(self, plot_number: str, cooperative_id: UUID) -> LandPlot | None:
        """Get land plot by plot number within cooperative."""
        query = select(LandPlotModel).where(
            LandPlotModel.plot_number == plot_number,
            LandPlotModel.cooperative_id == cooperative_id,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def add(self, entity: LandPlot) -> LandPlot:
        """Add new land plot."""
        model = LandPlotModel.from_domain(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def update(self, entity: LandPlot) -> LandPlot:
        """Update existing land plot."""
        query = select(LandPlotModel).where(LandPlotModel.id == entity.id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if model is None:
            raise ValueError(f"LandPlot with id {entity.id} not found")

        model.plot_number = entity.plot_number
        model.area_sqm = entity.area_sqm
        model.cadastral_number = entity.cadastral_number
        model.status = entity.status
        
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete land plot by ID."""
        query = select(LandPlotModel).where(
            LandPlotModel.id == id,
            LandPlotModel.cooperative_id == cooperative_id,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if model:
            await self.session.delete(model)
            await self.session.commit()


class OwnerRepository(IOwnerRepository):
    """SQLAlchemy implementation of Owner repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> Owner | None:
        """Get owner by ID. Note: cooperative_id not used for owners."""
        query = select(OwnerModel).where(OwnerModel.id == id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_all(self, cooperative_id: UUID) -> list[Owner]:
        """Get all owners. Note: cooperative_id not used for owners."""
        query = select(OwnerModel)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def search_by_name_or_tax_id(self, query: str, limit: int = 100) -> list[Owner]:
        """Search owners by name or tax_id."""
        from sqlalchemy import or_
        
        search_pattern = f"%{query}%"
        stmt = (
            select(OwnerModel)
            .where(
                or_(
                    OwnerModel.name.ilike(search_pattern),
                    OwnerModel.tax_id.ilike(search_pattern),
                )
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def add(self, entity: Owner) -> Owner:
        """Add new owner."""
        model = OwnerModel.from_domain(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def update(self, entity: Owner) -> Owner:
        """Update existing owner."""
        query = select(OwnerModel).where(OwnerModel.id == entity.id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if model is None:
            raise ValueError(f"Owner with id {entity.id} not found")

        model.owner_type = entity.owner_type
        model.name = entity.name
        model.tax_id = entity.tax_id
        model.contact_phone = entity.contact_phone
        model.contact_email = entity.contact_email
        
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete owner by ID."""
        query = select(OwnerModel).where(OwnerModel.id == id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if model:
            await self.session.delete(model)
            await self.session.commit()


class PlotOwnershipRepository(IPlotOwnershipRepository):
    """SQLAlchemy implementation of PlotOwnership repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> PlotOwnership | None:
        """Get plot ownership by ID, filtered by cooperative via land_plot."""
        query = (
            select(PlotOwnershipModel)
            .join(LandPlotModel, PlotOwnershipModel.land_plot_id == LandPlotModel.id)
            .where(
                PlotOwnershipModel.id == id,
                LandPlotModel.cooperative_id == cooperative_id,
            )
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_land_plot(self, land_plot_id: UUID, cooperative_id: UUID) -> list[PlotOwnership]:
        """Get all ownerships for a land plot."""
        query = select(PlotOwnershipModel).where(
            PlotOwnershipModel.land_plot_id == land_plot_id
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def get_by_owner(self, owner_id: UUID, cooperative_id: UUID) -> list[PlotOwnership]:
        """Get all ownerships for an owner."""
        query = (
            select(PlotOwnershipModel)
            .join(LandPlotModel, PlotOwnershipModel.land_plot_id == LandPlotModel.id)
            .where(
                PlotOwnershipModel.owner_id == owner_id,
                LandPlotModel.cooperative_id == cooperative_id,
            )
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def get_current_ownerships(self, land_plot_id: UUID) -> list[PlotOwnership]:
        """Get current (non-closed) ownerships for a land plot."""
        query = select(PlotOwnershipModel).where(
            PlotOwnershipModel.land_plot_id == land_plot_id,
            PlotOwnershipModel.valid_to.is_(None),
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def add(self, entity: PlotOwnership) -> PlotOwnership:
        """Add new plot ownership."""
        model = PlotOwnershipModel.from_domain(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def update(self, entity: PlotOwnership) -> PlotOwnership:
        """Update existing plot ownership."""
        query = select(PlotOwnershipModel).where(PlotOwnershipModel.id == entity.id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if model is None:
            raise ValueError(f"PlotOwnership with id {entity.id} not found")

        model.share_numerator = entity.share_numerator
        model.share_denominator = entity.share_denominator
        model.is_primary = entity.is_primary
        model.valid_from = entity.valid_from
        model.valid_to = entity.valid_to
        
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete plot ownership by ID."""
        query = (
            select(PlotOwnershipModel)
            .join(LandPlotModel, PlotOwnershipModel.land_plot_id == LandPlotModel.id)
            .where(
                PlotOwnershipModel.id == id,
                LandPlotModel.cooperative_id == cooperative_id,
            )
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if model:
            await self.session.delete(model)
            await self.session.commit()
