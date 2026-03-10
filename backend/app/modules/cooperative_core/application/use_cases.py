"""Use cases for cooperative_core module."""

from uuid import UUID

from app.modules.shared.kernel.exceptions import ValidationError

from ..domain.entities import Cooperative
from ..domain.repositories import ICooperativeRepository
from .dtos import CooperativeCreate, CooperativeUpdate


class CreateCooperativeUseCase:
    """Use case for creating a new Cooperative."""

    def __init__(self, repo: ICooperativeRepository):
        self.repo = repo

    async def execute(self, data: CooperativeCreate) -> Cooperative:
        """Create a new cooperative.

        Args:
            data: DTO with cooperative data.

        Returns:
            Created Cooperative entity.

        Raises:
            ValidationError: If validation fails.
        """
        # Domain validation
        if not data.name or len(data.name) > 255:
            raise ValidationError("Name must be between 1 and 255 characters")

        if data.unp and len(data.unp) > 20:
            raise ValidationError("UNP must not exceed 20 characters")

        if data.address and len(data.address) > 512:
            raise ValidationError("Address must not exceed 512 characters")

        entity = Cooperative(
            id=UUID(int=0),  # Will be set by repository
            name=data.name,
            unp=data.unp,
            address=data.address,
        )

        return await self.repo.add(entity)


class GetCooperativeUseCase:
    """Use case for getting a Cooperative by ID."""

    def __init__(self, repo: ICooperativeRepository):
        self.repo = repo

    async def execute(
        self, cooperative_id: UUID, current_cooperative_id: UUID | None
    ) -> Cooperative | None:
        """Get cooperative by ID.

        Args:
            cooperative_id: ID of cooperative to get.
            current_cooperative_id: ID of current user's cooperative (None for admin).

        Returns:
            Cooperative entity or None.
        """
        return await self.repo.get_by_id(cooperative_id, current_cooperative_id)


class GetCooperativesUseCase:
    """Use case for getting list of Cooperatives."""

    def __init__(self, repo: ICooperativeRepository):
        self.repo = repo

    async def execute(self, cooperative_id: UUID | None) -> list[Cooperative]:
        """Get list of cooperatives.

        Args:
            cooperative_id: Filter by cooperative ID. None for all (admin).

        Returns:
            List of Cooperative entities.
        """
        if cooperative_id is None:
            # Admin case - get all cooperatives
            # For this we need special handling in repository
            return await self.repo.get_all_for_admin()
        return await self.repo.get_all(cooperative_id)


class UpdateCooperativeUseCase:
    """Use case for updating a Cooperative."""

    def __init__(self, repo: ICooperativeRepository):
        self.repo = repo

    async def execute(
        self,
        cooperative_id: UUID,
        data: CooperativeUpdate,
        current_cooperative_id: UUID,
    ) -> Cooperative | None:
        """Update cooperative.

        Args:
            cooperative_id: ID of cooperative to update.
            data: DTO with update data.
            current_cooperative_id: ID of current user's cooperative.

        Returns:
            Updated Cooperative entity or None.
        """
        entity = await self.repo.get_by_id(cooperative_id, current_cooperative_id)
        if entity is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(entity, field):
                setattr(entity, field, value)

        return await self.repo.update(entity)


class DeleteCooperativeUseCase:
    """Use case for deleting a Cooperative."""

    def __init__(self, repo: ICooperativeRepository):
        self.repo = repo

    async def execute(self, cooperative_id: UUID, current_cooperative_id: UUID) -> bool:
        """Delete cooperative by ID.

        Args:
            cooperative_id: ID of cooperative to delete.
            current_cooperative_id: ID of current user's cooperative.

        Returns:
            True if deleted, False if not found.
        """
        entity = await self.repo.get_by_id(cooperative_id, current_cooperative_id)
        if entity is None:
            return False

        await self.repo.delete(cooperative_id, current_cooperative_id)
        return True
