"""Use cases for payments module."""

from uuid import UUID

from app.modules.shared.kernel.exceptions import ValidationError

from .dtos import PaymentCreate
from ..domain.entities import Payment
from ..domain.repositories import IPaymentRepository


class RegisterPaymentUseCase:
    """Use case for registering a Payment."""

    def __init__(self, repo: IPaymentRepository):
        self.repo = repo

    async def execute(self, data: PaymentCreate, cooperative_id: UUID) -> Payment:
        """Register a new payment."""
        # Domain validation
        if data.amount <= 0:
            raise ValidationError("Amount must be positive")

        entity = Payment(
            id=UUID(int=0),
            financial_subject_id=data.financial_subject_id,
            payer_owner_id=data.payer_owner_id,
            amount=data.amount,
            payment_date=data.payment_date,
            document_number=data.document_number,
            description=data.description,
            status="confirmed",
        )
        
        return await self.repo.add(entity)


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

    def __init__(self, repo: IPaymentRepository):
        self.repo = repo

    async def execute(self, payment_id: UUID, cooperative_id: UUID) -> Payment:
        """Cancel payment (change status to 'cancelled')."""
        payment = await self.repo.get_by_id(payment_id, cooperative_id)
        
        if payment is None:
            raise ValidationError("Payment not found")
        
        if payment.status == "cancelled":
            raise ValidationError("Payment is already cancelled")

        payment.status = "cancelled"
        return await self.repo.update(payment)
