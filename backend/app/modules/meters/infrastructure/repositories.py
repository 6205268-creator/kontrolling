"""Meters repository implementations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.meters.domain.entities import Meter, MeterReading
from app.modules.meters.domain.repositories import IMeterRepository, IMeterReadingRepository

from .models import MeterModel, MeterReadingModel


class MeterRepository(IMeterRepository):
    """SQLAlchemy implementation of Meter repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> Meter | None:
        """Get meter by ID. Note: cooperative_id filtering requires owner lookup."""
        from app.modules.land_management.infrastructure.models import OwnerModel
        from app.modules.land_management.infrastructure.models import PlotOwnershipModel
        from app.modules.land_management.infrastructure.models import LandPlotModel
        
        # Join through owner -> plot_ownership -> land_plot to filter by cooperative
        query = (
            select(MeterModel)
            .join(OwnerModel, MeterModel.owner_id == OwnerModel.id)
            .join(PlotOwnershipModel, OwnerModel.id == PlotOwnershipModel.owner_id)
            .join(LandPlotModel, PlotOwnershipModel.land_plot_id == LandPlotModel.id)
            .where(
                MeterModel.id == id,
                LandPlotModel.cooperative_id == cooperative_id,
            )
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_owner(self, owner_id: UUID, cooperative_id: UUID) -> list[Meter]:
        """Get all meters for an owner."""
        query = select(MeterModel).where(MeterModel.owner_id == owner_id)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def add(self, entity: Meter) -> Meter:
        """Add new meter."""
        model = MeterModel.from_domain(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def update(self, entity: Meter) -> Meter:
        """Update existing meter."""
        query = select(MeterModel).where(MeterModel.id == entity.id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Meter with id {entity.id} not found")
        
        model.meter_type = entity.meter_type
        model.serial_number = entity.serial_number
        model.installation_date = entity.installation_date
        model.status = entity.status
        
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete meter by ID."""
        query = select(MeterModel).where(MeterModel.id == id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.commit()


class MeterReadingRepository(IMeterReadingRepository):
    """SQLAlchemy implementation of MeterReading repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_meter(self, meter_id: UUID) -> list[MeterReading]:
        """Get all readings for a meter."""
        query = (
            select(MeterReadingModel)
            .where(MeterReadingModel.meter_id == meter_id)
            .order_by(MeterReadingModel.reading_date.desc())
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def add(self, entity: MeterReading) -> MeterReading:
        """Add new meter reading."""
        model = MeterReadingModel.from_domain(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()
