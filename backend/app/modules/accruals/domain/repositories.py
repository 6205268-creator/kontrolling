"""Accruals domain repository interfaces.

Pure Python - no framework dependencies (FastAPI, SQLAlchemy, Pydantic).
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.shared.kernel.repositories import IRepository

from .entities import Accrual, ContributionType


class IAccrualRepository(IRepository[Accrual], ABC):
    """Repository interface for Accrual operations."""

    @abstractmethod
    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> Accrual | None:
        """Get accrual by ID, filtered by cooperative via financial_subject."""
        pass

    @abstractmethod
    async def get_by_financial_subject(
        self,
        financial_subject_id: UUID,
        cooperative_id: UUID,
    ) -> list[Accrual]:
        """Get all accruals for a financial subject."""
        pass

    @abstractmethod
    async def get_by_cooperative(self, cooperative_id: UUID) -> list[Accrual]:
        """Get all accruals for a cooperative."""
        pass

    @abstractmethod
    async def add(self, entity: Accrual) -> Accrual:
        """Add new accrual."""
        pass

    @abstractmethod
    async def update(self, entity: Accrual) -> Accrual:
        """Update existing accrual."""
        pass

    @abstractmethod
    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete accrual by ID."""
        pass


class IContributionTypeRepository(IRepository[ContributionType], ABC):
    """Repository interface for ContributionType operations."""

    @abstractmethod
    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> ContributionType | None:
        """Get contribution type by ID."""
        pass

    @abstractmethod
    async def get_all(self, cooperative_id: UUID) -> list[ContributionType]:
        """Get all contribution types."""
        pass

    @abstractmethod
    async def get_by_code(self, code: str) -> ContributionType | None:
        """Get contribution type by code."""
        pass

    @abstractmethod
    async def add(self, entity: ContributionType) -> ContributionType:
        """Add new contribution type."""
        pass

    @abstractmethod
    async def update(self, entity: ContributionType) -> ContributionType:
        """Update existing contribution type."""
        pass

    @abstractmethod
    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete contribution type by ID."""
        pass
