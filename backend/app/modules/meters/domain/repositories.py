"""Meters domain repository interfaces."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.shared.kernel.repositories import IRepository

from .entities import Meter, MeterReading


class IMeterRepository(IRepository[Meter], ABC):
    """Repository interface for Meter operations."""

    @abstractmethod
    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> Meter | None:
        pass

    @abstractmethod
    async def get_by_owner(self, owner_id: UUID, cooperative_id: UUID) -> list[Meter]:
        pass

    @abstractmethod
    async def add(self, entity: Meter) -> Meter:
        pass

    @abstractmethod
    async def update(self, entity: Meter) -> Meter:
        pass

    @abstractmethod
    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        pass


class IMeterReadingRepository(IRepository[MeterReading], ABC):
    """Repository interface for MeterReading operations."""

    @abstractmethod
    async def get_by_meter(self, meter_id: UUID) -> list[MeterReading]:
        pass

    @abstractmethod
    async def add(self, entity: MeterReading) -> MeterReading:
        pass
