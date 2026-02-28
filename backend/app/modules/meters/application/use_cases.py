"""Use cases for meters module."""

from uuid import UUID

from app.modules.shared.kernel.exceptions import ValidationError

from .dtos import MeterCreate, MeterReadingCreate
from ..domain.entities import Meter, MeterReading
from ..domain.repositories import IMeterRepository, IMeterReadingRepository


class CreateMeterUseCase:
    """Use case for creating a Meter."""

    def __init__(self, repo: IMeterRepository):
        self.repo = repo

    async def execute(self, data: MeterCreate, cooperative_id: UUID) -> Meter:
        """Create a new meter."""
        entity = Meter(
            id=UUID(int=0),
            owner_id=data.owner_id,
            meter_type=data.meter_type,
            serial_number=data.serial_number,
            installation_date=data.installation_date,
            status=data.status,
        )
        return await self.repo.add(entity)


class GetMeterUseCase:
    """Use case for getting a Meter by ID."""

    def __init__(self, repo: IMeterRepository):
        self.repo = repo

    async def execute(self, meter_id: UUID, cooperative_id: UUID) -> Meter | None:
        """Get meter by ID."""
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

    def __init__(self, repo: IMeterReadingRepository):
        self.repo = repo

    async def execute(self, data: MeterReadingCreate) -> MeterReading:
        """Add a meter reading."""
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
