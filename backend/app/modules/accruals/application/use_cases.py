"""Use cases for accruals module."""

from uuid import UUID

from app.modules.shared.kernel.exceptions import ValidationError

from .dtos import AccrualCreate, AccrualUpdate
from ..domain.entities import Accrual
from ..domain.repositories import IAccrualRepository, IContributionTypeRepository


class CreateAccrualUseCase:
    """Use case for creating an Accrual."""

    def __init__(self, accrual_repo: IAccrualRepository, fs_repo=None):
        self.accrual_repo = accrual_repo
        self.fs_repo = fs_repo

    async def execute(self, data: AccrualCreate, cooperative_id: UUID) -> Accrual:
        """Create a new accrual.

        Args:
            data: DTO with accrual data.
            cooperative_id: ID of cooperative for access control.

        Returns:
            Created Accrual entity.

        Raises:
            ValidationError: If financial subject doesn't belong to cooperative.
        """
        # Verify financial subject belongs to cooperative
        if self.fs_repo:
            fs = await self.fs_repo.get_by_id(data.financial_subject_id, cooperative_id)
            if fs is None:
                raise ValidationError("Financial subject does not belong to the specified cooperative")

        # Domain validation
        if data.amount < 0:
            raise ValidationError("Amount must be non-negative")

        entity = Accrual(
            financial_subject_id=data.financial_subject_id,
            contribution_type_id=data.contribution_type_id,
            amount=data.amount,
            accrual_date=data.accrual_date,
            period_start=data.period_start,
            period_end=data.period_end,
            status="created",
        )

        return await self.accrual_repo.add(entity)


class GetAccrualUseCase:
    """Use case for getting an Accrual by ID."""

    def __init__(self, repo: IAccrualRepository):
        self.repo = repo

    async def execute(self, accrual_id: UUID, cooperative_id: UUID) -> Accrual | None:
        """Get accrual by ID."""
        return await self.repo.get_by_id(accrual_id, cooperative_id)


class GetAccrualsByFinancialSubjectUseCase:
    """Use case for getting accruals by financial subject."""

    def __init__(self, repo: IAccrualRepository):
        self.repo = repo

    async def execute(
        self,
        financial_subject_id: UUID,
        cooperative_id: UUID,
    ) -> list[Accrual]:
        """Get all accruals for a financial subject."""
        return await self.repo.get_by_financial_subject(financial_subject_id, cooperative_id)


class GetAccrualsByCooperativeUseCase:
    """Use case for getting accruals by cooperative."""

    def __init__(self, repo: IAccrualRepository):
        self.repo = repo

    async def execute(self, cooperative_id: UUID) -> list[Accrual]:
        """Get all accruals for a cooperative."""
        return await self.repo.get_by_cooperative(cooperative_id)


class ApplyAccrualUseCase:
    """Use case for applying an accrual (status: created → applied)."""

    def __init__(self, repo: IAccrualRepository):
        self.repo = repo

    async def execute(self, accrual_id: UUID, cooperative_id: UUID) -> Accrual:
        """Apply accrual (change status to 'applied').
        
        Args:
            accrual_id: ID of accrual to apply.
            cooperative_id: ID of cooperative for access control.
            
        Returns:
            Updated Accrual entity.
            
        Raises:
            ValidationError: If accrual not found or invalid status.
        """
        accrual = await self.repo.get_by_id(accrual_id, cooperative_id)
        
        if accrual is None:
            raise ValidationError("Accrual not found")
        
        if accrual.status != "created":
            raise ValidationError(
                f"Cannot apply accrual with status '{accrual.status}'. Only 'created' status allowed."
            )

        accrual.status = "applied"
        return await self.repo.update(accrual)


class CancelAccrualUseCase:
    """Use case for cancelling an accrual (status → cancelled)."""

    def __init__(self, repo: IAccrualRepository):
        self.repo = repo

    async def execute(self, accrual_id: UUID, cooperative_id: UUID) -> Accrual:
        """Cancel accrual (change status to 'cancelled').
        
        Args:
            accrual_id: ID of accrual to cancel.
            cooperative_id: ID of cooperative for access control.
            
        Returns:
            Updated Accrual entity.
            
        Raises:
            ValidationError: If accrual not found or already cancelled.
        """
        accrual = await self.repo.get_by_id(accrual_id, cooperative_id)
        
        if accrual is None:
            raise ValidationError("Accrual not found")
        
        if accrual.status == "cancelled":
            raise ValidationError("Accrual is already cancelled")

        accrual.status = "cancelled"
        return await self.repo.update(accrual)


class MassCreateAccrualsUseCase:
    """Use case for mass creating accruals."""

    def __init__(self, accrual_repo: IAccrualRepository, fs_repo=None):
        self.accrual_repo = accrual_repo
        self.fs_repo = fs_repo

    async def execute(
        self,
        accruals_data: list[AccrualCreate],
        cooperative_id: UUID,
    ) -> list[Accrual]:
        """Create multiple accruals in one transaction.

        Args:
            accruals_data: List of DTOs with accrual data.
            cooperative_id: ID of cooperative for access control.

        Returns:
            List of created Accrual entities.
            
        Raises:
            ValidationError: If any financial subject doesn't belong to cooperative.
        """
        created_accruals = []

        for data in accruals_data:
            # Verify financial subject belongs to cooperative
            if self.fs_repo:
                fs = await self.fs_repo.get_by_id(data.financial_subject_id, cooperative_id)
                if fs is None:
                    raise ValidationError("Financial subject does not belong to the specified cooperative")
            
            entity = Accrual(
                financial_subject_id=data.financial_subject_id,
                contribution_type_id=data.contribution_type_id,
                amount=data.amount,
                accrual_date=data.accrual_date,
                period_start=data.period_start,
                period_end=data.period_end,
                status="created",
            )
            created = await self.accrual_repo.add(entity)
            created_accruals.append(created)

        return created_accruals


class GetContributionTypesUseCase:
    """Use case for getting all contribution types."""

    def __init__(self, repo: IContributionTypeRepository):
        self.repo = repo

    async def execute(self) -> list:
        """Get all contribution types."""
        return await self.repo.get_all(UUID(int=0))  # cooperative_id not used for contribution types
