"""Payments repository implementations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.payments.domain.entities import Payment
from app.modules.payments.domain.repositories import IPaymentRepository

from .models import PaymentModel


class PaymentRepository(IPaymentRepository):
    """SQLAlchemy implementation of Payment repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> Payment | None:
        """Get payment by ID, filtered by cooperative via financial_subject."""
        from app.modules.financial_core.infrastructure.models import FinancialSubjectModel

        query = (
            select(PaymentModel)
            .join(
                FinancialSubjectModel, PaymentModel.financial_subject_id == FinancialSubjectModel.id
            )
            .where(
                PaymentModel.id == id,
                FinancialSubjectModel.cooperative_id == cooperative_id,
            )
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_financial_subject(
        self,
        financial_subject_id: UUID,
        cooperative_id: UUID,
    ) -> list[Payment]:
        """Get all payments for a financial subject."""
        from app.modules.financial_core.infrastructure.models import FinancialSubjectModel

        query = (
            select(PaymentModel)
            .join(
                FinancialSubjectModel, PaymentModel.financial_subject_id == FinancialSubjectModel.id
            )
            .where(
                PaymentModel.financial_subject_id == financial_subject_id,
                FinancialSubjectModel.cooperative_id == cooperative_id,
            )
            .order_by(PaymentModel.payment_date.desc())
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def get_by_owner(self, owner_id: UUID, cooperative_id: UUID) -> list[Payment]:
        """Get all payments for an owner."""
        from app.modules.financial_core.infrastructure.models import FinancialSubjectModel

        query = (
            select(PaymentModel)
            .join(
                FinancialSubjectModel, PaymentModel.financial_subject_id == FinancialSubjectModel.id
            )
            .where(
                PaymentModel.payer_owner_id == owner_id,
                FinancialSubjectModel.cooperative_id == cooperative_id,
            )
            .order_by(PaymentModel.payment_date.desc())
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def get_by_cooperative(self, cooperative_id: UUID) -> list[Payment]:
        """Get all payments for a cooperative."""
        from app.modules.financial_core.infrastructure.models import FinancialSubjectModel

        query = (
            select(PaymentModel)
            .join(
                FinancialSubjectModel, PaymentModel.financial_subject_id == FinancialSubjectModel.id
            )
            .where(FinancialSubjectModel.cooperative_id == cooperative_id)
            .order_by(PaymentModel.payment_date.desc())
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def get_all(self, cooperative_id: UUID) -> list[Payment]:
        """Get all payments for a cooperative (alias for get_by_cooperative)."""
        return await self.get_by_cooperative(cooperative_id)

    async def add(self, entity: Payment) -> Payment:
        """Add new payment."""
        model = PaymentModel.from_domain(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def update(self, entity: Payment) -> Payment:
        """Update existing payment.

        Note: amount is immutable - not updated to preserve financial integrity.
        """
        query = select(PaymentModel).where(PaymentModel.id == entity.id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(f"Payment with id {entity.id} not found")

        model.financial_subject_id = entity.financial_subject_id
        model.payer_owner_id = entity.payer_owner_id
        # amount is immutable - not updated
        model.payment_date = entity.payment_date
        model.document_number = entity.document_number
        model.description = entity.description
        model.status = entity.status
        model.cancelled_at = entity.cancelled_at
        model.cancelled_by_user_id = entity.cancelled_by_user_id
        model.cancellation_reason = entity.cancellation_reason

        await self.session.commit()

        # Re-fetch to get fresh data from DB (amount should be unchanged)
        self.session.expunge(model)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain()

    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete payment by ID."""
        from app.modules.financial_core.infrastructure.models import FinancialSubjectModel

        query = (
            select(PaymentModel)
            .join(
                FinancialSubjectModel, PaymentModel.financial_subject_id == FinancialSubjectModel.id
            )
            .where(
                PaymentModel.id == id,
                FinancialSubjectModel.cooperative_id == cooperative_id,
            )
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.commit()
