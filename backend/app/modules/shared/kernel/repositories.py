"""Repository abstractions for domain layer.

Pure Python - no framework dependencies (FastAPI, SQLAlchemy, Pydantic).
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

from .entities import BaseEntity

T = TypeVar("T", bound=BaseEntity)


class IRepository(ABC, Generic[T]):
    """Generic repository interface for CRUD operations.
    
    All repository methods should filter by cooperative_id for multitenancy.
    """

    @abstractmethod
    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> T | None:
        """Get entity by ID, filtered by cooperative."""
        pass

    @abstractmethod
    async def get_all(self, cooperative_id: UUID) -> list[T]:
        """Get all entities for cooperative."""
        pass

    @abstractmethod
    async def add(self, entity: T) -> T:
        """Add new entity."""
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update existing entity."""
        pass

    @abstractmethod
    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete entity by ID."""
        pass
