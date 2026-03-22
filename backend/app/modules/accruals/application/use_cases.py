"""Use cases for accruals module."""

from datetime import datetime
from uuid import UUID, uuid4

from app.modules.shared.kernel.events import EventDispatcher
from app.modules.shared.kernel.exceptions import ValidationError

from ..domain.entities import Accrual
from ..domain.events import AccrualApplied, AccrualCancelled
from ..domain.repositories import IAccrualRepository, IContributionTypeRepository
from .dtos import AccrualCreate


class CreateAccrualUseCase:
    """Use case for creating an Accrual."""

    def __init__(self, accrual_repo: IAccrualRepository, fs_repo=None, period_guard=None):
        self.accrual_repo = accrual_repo
        self.fs_repo = fs_repo
        self.period_guard = period_guard

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
                raise ValidationError(
                    "Financial subject does not belong to the specified cooperative"
                )

        if self.period_guard:
            await self.period_guard.ensure_open_for_date(cooperative_id, data.accrual_date)

        # Domain validation
        if data.amount < 0:
            raise ValidationError("Amount must be non-negative")

        operation_number = (
            data.operation_number.strip()
            if data.operation_number
            else f"ACC-{cooperative_id.hex[:8]}-{uuid4().hex[:8]}"
        )
        entity = Accrual(
            financial_subject_id=data.financial_subject_id,
            contribution_type_id=data.contribution_type_id,
            amount=data.amount,
            accrual_date=data.accrual_date,
            period_start=data.period_start,
            period_end=data.period_end,
            due_date=data.due_date,
            status="created",
            operation_number=operation_number,
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

    def __init__(
        self,
        repo: IAccrualRepository,
        event_dispatcher: EventDispatcher | None = None,
        period_guard=None,
    ):
        self.repo = repo
        self.event_dispatcher = event_dispatcher
        self.period_guard = period_guard

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

        if self.period_guard:
            await self.period_guard.ensure_open_for_date(cooperative_id, accrual.accrual_date)

        accrual.status = "applied"
        result = await self.repo.update(accrual)

        # Dispatch domain event
        if self.event_dispatcher:
            self.event_dispatcher.dispatch(
                AccrualApplied(
                    accrual_id=result.id,
                    cooperative_id=cooperative_id,
                    financial_subject_id=result.financial_subject_id,
                    contribution_type_id=result.contribution_type_id,
                    amount=result.amount,
                    accrual_date=result.accrual_date,
                    due_date=result.due_date,
                    operation_number=result.operation_number,
                )
            )

        return result


class CancelAccrualUseCase:
    """Use case for cancelling an accrual (status → cancelled)."""

    def __init__(
        self,
        repo: IAccrualRepository,
        event_dispatcher: EventDispatcher | None = None,
        period_guard=None,
    ):
        self.repo = repo
        self.event_dispatcher = event_dispatcher
        self.period_guard = period_guard

    async def execute(
        self,
        accrual_id: UUID,
        cooperative_id: UUID,
        cancelled_by_user_id: UUID,
        cancellation_reason: str | None = None,
        cancelled_at: datetime | None = None,
    ) -> Accrual:
        """Cancel accrual (change status to 'cancelled').

        Args:
            accrual_id: ID of accrual to cancel.
            cooperative_id: ID of cooperative for access control.
            cancelled_by_user_id: ID of user cancelling the accrual.
            cancellation_reason: Reason for cancellation (optional).
            cancelled_at: Cancellation datetime (defaults to now).

        Returns:
            Updated Accrual entity.

        Raises:
            ValidationError: If accrual not found or already cancelled.
        """
        from datetime import UTC, datetime

        accrual = await self.repo.get_by_id(accrual_id, cooperative_id)

        if accrual is None:
            raise ValidationError("Accrual not found")

        # Use entity method for cancellation (Rich Domain pattern)
        accrual.cancel(
            cancelled_by=cancelled_by_user_id,
            reason=cancellation_reason,
            now=cancelled_at or datetime.now(UTC),
        )
        result = await self.repo.update(accrual)

        # Dispatch domain event
        if self.event_dispatcher:
            self.event_dispatcher.dispatch(
                AccrualCancelled(
                    accrual_id=result.id,
                    cancelled_at=result.cancelled_at,
                    cancelled_by=result.cancelled_by_user_id,
                    reason=result.cancellation_reason,
                )
            )

        return result


class MassCreateAccrualsUseCase:
    """Use case for mass creating accruals."""

    def __init__(self, accrual_repo: IAccrualRepository, fs_repo=None, period_guard=None):
        self.accrual_repo = accrual_repo
        self.fs_repo = fs_repo
        self.period_guard = period_guard

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
                    raise ValidationError(
                        "Financial subject does not belong to the specified cooperative"
                    )

            if self.period_guard:
                await self.period_guard.ensure_open_for_date(cooperative_id, data.accrual_date)

            operation_number = f"ACC-{cooperative_id.hex[:8]}-{uuid4().hex[:8]}"
            entity = Accrual(
                financial_subject_id=data.financial_subject_id,
                contribution_type_id=data.contribution_type_id,
                amount=data.amount,
                accrual_date=data.accrual_date,
                period_start=data.period_start,
                period_end=data.period_end,
                due_date=data.due_date,
                status="created",
                operation_number=operation_number,
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
        return await self.repo.get_all(
            UUID(int=0)
        )  # cooperative_id not used for contribution types
