"""Cooperative domain repository interfaces.

Pure Python - no framework dependencies (FastAPI, SQLAlchemy, Pydantic).
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.shared.kernel.repositories import IRepository

from .entities import Cooperative


class ICooperativeRepository(IRepository[Cooperative], ABC):
    """Repository interface for Cooperative operations.

    All methods must filter by cooperative_id for multitenancy.
    """

    @abstractmethod
    async def get_by_id(self, id: UUID, cooperative_id: UUID | None) -> Cooperative | None:
        """Get cooperative by ID. cooperative_id None means admin — return by id only."""
        pass

    @abstractmethod
    async def get_all(self, cooperative_id: UUID) -> list[Cooperative]:
        """Get all cooperatives for given cooperative_id.

        For admin, cooperative_id can be None to get all.
        """
        pass

    @abstractmethod
    async def add(self, entity: Cooperative) -> Cooperative:
        """Add new cooperative."""
        pass

    @abstractmethod
    async def update(self, entity: Cooperative) -> Cooperative:
        """Update existing cooperative."""
        pass

    @abstractmethod
    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete cooperative by ID."""
        pass
