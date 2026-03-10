"""Use cases for meters module."""

from uuid import UUID

from app.modules.financial_core.domain.entities import FinancialSubject
from app.modules.financial_core.domain.repositories import IFinancialSubjectRepository
from app.modules.shared.kernel.events import EventDispatcher

from ..domain.entities import Meter, MeterReading
from ..domain.events import MeterCreated
from ..domain.repositories import IMeterReadingRepository, IMeterRepository
from .dtos import MeterCreate, MeterReadingCreate


class CreateMeterUseCase:
    """Use case for creating a Meter.

    Creates both Meter and FinancialSubject atomically.
    """

    def __init__(
        self,
        repo: IMeterRepository,
        fs_repo: IFinancialSubjectRepository,
        event_dispatcher: EventDispatcher,
    ):
        self.repo = repo
        self.fs_repo = fs_repo
        self.event_dispatcher = event_dispatcher

    async def execute(self, data: MeterCreate, cooperative_id: UUID | None) -> Meter:
        """Create a new meter."""
        # For admin users (cooperative_id=None), determine cooperative from owner's land plot
        if cooperative_id is None:
            from sqlalchemy import select

            from app.modules.land_management.infrastructure.models import (
                LandPlotModel,
                PlotOwnershipModel,
            )

            # Get cooperative from owner's land plot
            query = (
                select(LandPlotModel.cooperative_id)
                .join(PlotOwnershipModel, LandPlotModel.id == PlotOwnershipModel.land_plot_id)
                .where(PlotOwnershipModel.owner_id == data.owner_id)
                .limit(1)
            )
            # Need to get session from repo
            session = self.repo.session  # type: ignore[attr-defined]
            result = await session.execute(query)
            row = result.first()
            if row is None:
                raise ValueError(f"Owner with id {data.owner_id} has no land plots")
            cooperative_id = row[0]

        entity = Meter(
            id=UUID(int=0),
            owner_id=data.owner_id,
            meter_type=data.meter_type,
            serial_number=data.serial_number,
            installation_date=data.installation_date,
            status=data.status,
        )
        created_meter = await self.repo.add(entity)

        # Create FinancialSubject atomically
        fs_code = f"FS-M-{created_meter.serial_number}"
        subject_type = f"{created_meter.meter_type}_METER"
        fs = FinancialSubject(
            id=UUID(int=0),
            subject_type=subject_type,
            subject_id=created_meter.id,
            cooperative_id=cooperative_id,
            code=fs_code,
            status="active",
        )
        await self.fs_repo.add(fs)

        # Publish domain event for other modules
        self.event_dispatcher.dispatch(
            MeterCreated(
                meter_id=created_meter.id,
                cooperative_id=cooperative_id,
                meter_type=created_meter.meter_type,
                serial_number=created_meter.serial_number,
            )
        )

        return created_meter


class GetMeterUseCase:
    """Use case for getting a Meter by ID."""

    def __init__(self, repo: IMeterRepository):
        self.repo = repo

    async def execute(self, meter_id: UUID, cooperative_id: UUID | None) -> Meter | None:
        """Get meter by ID."""
        # For admin users (cooperative_id=None), determine cooperative from meter's owner
        if cooperative_id is None:
            from sqlalchemy import select

            from app.modules.land_management.infrastructure.models import (
                LandPlotModel,
                PlotOwnershipModel,
            )
            from app.modules.meters.infrastructure.models import MeterModel

            # Get cooperative from meter's owner land plot
            query = (
                select(LandPlotModel.cooperative_id)
                .join(PlotOwnershipModel, LandPlotModel.id == PlotOwnershipModel.land_plot_id)
                .join(MeterModel, MeterModel.owner_id == PlotOwnershipModel.owner_id)
                .where(MeterModel.id == meter_id)
                .limit(1)
            )
            session = self.repo.session  # type: ignore[attr-defined]
            result = await session.execute(query)
            row = result.first()
            if row is None:
                return None
            cooperative_id = row[0]

        return await self.repo.get_by_id(meter_id, cooperative_id)


class GetMetersByOwnerUseCase:
    """Use case for getting meters by owner."""

    def __init__(self, repo: IMeterRepository):
        self.repo = repo

    async def execute(self, owner_id: UUID, cooperative_id: UUID) -> list[Meter]:
        """Get all meters for an owner."""
        return await self.repo.get_by_owner(owner_id, cooperative_id)


class UpdateMeterUseCase:
    """Use case for updating a Meter."""

    def __init__(self, repo: IMeterRepository):
        self.repo = repo

    async def execute(self, meter_id: UUID, data, cooperative_id: UUID) -> Meter | None:
        """Update meter."""
        entity = await self.repo.get_by_id(meter_id, cooperative_id)
        if entity is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(entity, field):
                setattr(entity, field, value)

        return await self.repo.update(entity)


class DeleteMeterUseCase:
    """Use case for deleting a Meter."""

    def __init__(self, repo: IMeterRepository):
        self.repo = repo

    async def execute(self, meter_id: UUID, cooperative_id: UUID) -> bool:
        """Delete meter."""
        entity = await self.repo.get_by_id(meter_id, cooperative_id)
        if entity is None:
            return False
        await self.repo.delete(meter_id, cooperative_id)
        return True


class AddMeterReadingUseCase:
    """Use case for adding a meter reading."""

    def __init__(self, repo: IMeterReadingRepository, meter_repo: IMeterRepository):
        self.repo = repo
        self.meter_repo = meter_repo

    async def execute(self, data: MeterReadingCreate, cooperative_id: UUID | None) -> MeterReading:
        """Add a meter reading."""
        # For admin users (cooperative_id=None), determine cooperative from meter's owner
        if cooperative_id is None:
            from sqlalchemy import select

            from app.modules.land_management.infrastructure.models import (
                LandPlotModel,
                PlotOwnershipModel,
            )
            from app.modules.meters.infrastructure.models import MeterModel

            # Get cooperative from meter's owner land plot
            query = (
                select(LandPlotModel.cooperative_id)
                .join(PlotOwnershipModel, LandPlotModel.id == PlotOwnershipModel.land_plot_id)
                .join(MeterModel, MeterModel.owner_id == PlotOwnershipModel.owner_id)
                .where(MeterModel.id == data.meter_id)
                .limit(1)
            )
            session = self.meter_repo.session  # type: ignore[attr-defined]
            result = await session.execute(query)
            row = result.first()
            if row is None:
                raise ValueError(f"Meter with id {data.meter_id} not found")
            cooperative_id = row[0]

        # Verify meter exists and belongs to cooperative
        meter = await self.meter_repo.get_by_id(data.meter_id, cooperative_id)
        if meter is None:
            raise ValueError(f"Meter with id {data.meter_id} not found")

        entity = MeterReading(
            id=UUID(int=0),
            meter_id=data.meter_id,
            reading_value=data.reading_value,
            reading_date=data.reading_date,
        )
        return await self.repo.add(entity)


class GetMeterReadingsUseCase:
    """Use case for getting meter readings."""

    def __init__(self, repo: IMeterReadingRepository):
        self.repo = repo

    async def execute(self, meter_id: UUID) -> list[MeterReading]:
        """Get all readings for a meter."""
        return await self.repo.get_by_meter(meter_id)
