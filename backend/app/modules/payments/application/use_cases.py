"""Use cases for payments module."""

from datetime import datetime
from uuid import UUID, uuid4

from app.modules.shared.kernel.events import EventDispatcher
from app.modules.shared.kernel.exceptions import ValidationError

from ..domain.entities import Payment
from ..domain.events import PaymentCancelled, PaymentConfirmed
from ..domain.repositories import IPaymentRepository
from .dtos import PaymentCreate


class RegisterPaymentUseCase:
    """Use case for registering a Payment."""

    def __init__(
        self,
        repo: IPaymentRepository,
        event_dispatcher: EventDispatcher | None = None,
        fs_repo=None,
    ):
        self.repo = repo
        self.event_dispatcher = event_dispatcher
        self.fs_repo = fs_repo

    async def execute(self, data: PaymentCreate, cooperative_id: UUID) -> Payment:
        """Register a new payment.

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

        # Domain validation
        if data.amount <= 0:
            raise ValidationError("Amount must be positive")

        operation_number = f"PAY-{data.financial_subject_id.hex[:8]}-{uuid4().hex[:8]}"
        entity = Payment(
            id=UUID(int=0),
            financial_subject_id=data.financial_subject_id,
            payer_owner_id=data.payer_owner_id,
            amount=data.amount,
            payment_date=data.payment_date,
            document_number=data.document_number,
            description=data.description,
            status="confirmed",
            operation_number=operation_number,
        )

        result = await self.repo.add(entity)

        # Dispatch domain event
        if self.event_dispatcher:
            self.event_dispatcher.dispatch(
                PaymentConfirmed(
                    payment_id=result.id,
                    financial_subject_id=result.financial_subject_id,
                    payer_owner_id=result.payer_owner_id,
                    amount=result.amount,
                    payment_date=result.payment_date,
                    operation_number=result.operation_number,
                )
            )

        return result


class GetPaymentUseCase:
    """Use case for getting a Payment by ID."""

    def __init__(self, repo: IPaymentRepository):
        self.repo = repo

    async def execute(self, payment_id: UUID, cooperative_id: UUID) -> Payment | None:
        """Get payment by ID."""
        return await self.repo.get_by_id(payment_id, cooperative_id)


class GetPaymentsByFinancialSubjectUseCase:
    """Use case for getting payments by financial subject."""

    def __init__(self, repo: IPaymentRepository):
        self.repo = repo

    async def execute(
        self,
        financial_subject_id: UUID,
        cooperative_id: UUID,
    ) -> list[Payment]:
        """Get all payments for a financial subject."""
        return await self.repo.get_by_financial_subject(financial_subject_id, cooperative_id)


class GetPaymentsByOwnerUseCase:
    """Use case for getting payments by owner."""

    def __init__(self, repo: IPaymentRepository):
        self.repo = repo

    async def execute(self, owner_id: UUID, cooperative_id: UUID) -> list[Payment]:
        """Get all payments for an owner."""
        return await self.repo.get_by_owner(owner_id, cooperative_id)


class GetPaymentsByCooperativeUseCase:
    """Use case for getting payments by cooperative."""

    def __init__(self, repo: IPaymentRepository):
        self.repo = repo

    async def execute(self, cooperative_id: UUID) -> list[Payment]:
        """Get all payments for a cooperative."""
        return await self.repo.get_by_cooperative(cooperative_id)


class CancelPaymentUseCase:
    """Use case for cancelling a Payment."""

    def __init__(self, repo: IPaymentRepository, event_dispatcher: EventDispatcher | None = None):
        self.repo = repo
        self.event_dispatcher = event_dispatcher

    async def execute(
        self,
        payment_id: UUID,
        cooperative_id: UUID,
        cancelled_by_user_id: UUID,
        cancellation_reason: str | None = None,
        cancelled_at: datetime | None = None,
    ) -> Payment:
        """Cancel payment (change status to 'cancelled').

        Args:
            payment_id: ID of payment to cancel.
            cooperative_id: ID of cooperative for access control.
            cancelled_by_user_id: ID of user cancelling the payment.
            cancellation_reason: Reason for cancellation (optional).
            cancelled_at: Cancellation datetime (defaults to now).

        Returns:
            Updated Payment entity.

        Raises:
            ValidationError: If payment not found or already cancelled.
        """
        from datetime import UTC

        payment = await self.repo.get_by_id(payment_id, cooperative_id)

        if payment is None:
            raise ValidationError("Payment not found")

        # Use entity method for cancellation (Rich Domain pattern)
        payment.cancel(
            cancelled_by=cancelled_by_user_id,
            reason=cancellation_reason,
            now=cancelled_at or datetime.now(UTC),
        )
        result = await self.repo.update(payment)

        # Dispatch domain event
        if self.event_dispatcher:
            self.event_dispatcher.dispatch(
                PaymentCancelled(
                    payment_id=result.id,
                    cancelled_at=result.cancelled_at,
                    cancelled_by=result.cancelled_by_user_id,
                    reason=result.cancellation_reason,
                )
            )

        return result
