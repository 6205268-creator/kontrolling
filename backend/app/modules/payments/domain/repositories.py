"""Payments domain repository interfaces.

Pure Python - no framework dependencies.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.shared.kernel.repositories import IRepository

from .entities import Payment


class IPaymentRepository(IRepository[Payment], ABC):
    """Repository interface for Payment operations."""

    @abstractmethod
    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> Payment | None:
        """Get payment by ID, filtered by cooperative via financial_subject."""
        pass

    @abstractmethod
    async def get_by_financial_subject(
        self,
        financial_subject_id: UUID,
        cooperative_id: UUID,
    ) -> list[Payment]:
        """Get all payments for a financial subject."""
        pass

    @abstractmethod
    async def get_by_owner(self, owner_id: UUID, cooperative_id: UUID) -> list[Payment]:
        """Get all payments for an owner."""
        pass

    @abstractmethod
    async def get_by_cooperative(self, cooperative_id: UUID) -> list[Payment]:
        """Get all payments for a cooperative."""
        pass

    @abstractmethod
    async def add(self, entity: Payment) -> Payment:
        """Add new payment."""
        pass

    @abstractmethod
    async def update(self, entity: Payment) -> Payment:
        """Update existing payment."""
        pass

    @abstractmethod
    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete payment by ID."""
        pass
