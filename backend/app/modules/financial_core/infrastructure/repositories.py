"""Financial Core repository implementations.

SQLAlchemy implementation of financial core repositories.
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.financial_core.domain.entities import Balance, FinancialSubject
from app.modules.financial_core.domain.repositories import (
    IFinancialSubjectRepository,
    IBalanceRepository,
)

from .models import FinancialSubjectModel


class FinancialSubjectRepository(IFinancialSubjectRepository):
    """SQLAlchemy implementation of FinancialSubject repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> FinancialSubject | None:
        """Get financial subject by ID, filtered by cooperative."""
        query = select(FinancialSubjectModel).where(
            FinancialSubjectModel.id == id,
            FinancialSubjectModel.cooperative_id == cooperative_id,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_all(self, cooperative_id: UUID) -> list[FinancialSubject]:
        """Get all financial subjects for cooperative."""
        query = select(FinancialSubjectModel).where(
            FinancialSubjectModel.cooperative_id == cooperative_id
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def get_by_subject(
        self,
        subject_type: str,
        subject_id: UUID,
        cooperative_id: UUID,
    ) -> FinancialSubject | None:
        """Get financial subject by subject type and ID."""
        query = select(FinancialSubjectModel).where(
            FinancialSubjectModel.subject_type == subject_type,
            FinancialSubjectModel.subject_id == subject_id,
            FinancialSubjectModel.cooperative_id == cooperative_id,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def add(self, entity: FinancialSubject) -> FinancialSubject:
        """Add new financial subject."""
        model = FinancialSubjectModel.from_domain(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def update(self, entity: FinancialSubject) -> FinancialSubject:
        """Update existing financial subject."""
        query = select(FinancialSubjectModel).where(FinancialSubjectModel.id == entity.id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if model is None:
            raise ValueError(f"FinancialSubject with id {entity.id} not found")

        model.subject_type = entity.subject_type
        model.subject_id = entity.subject_id
        model.cooperative_id = entity.cooperative_id
        model.code = entity.code
        model.status = entity.status
        
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete financial subject by ID."""
        query = select(FinancialSubjectModel).where(
            FinancialSubjectModel.id == id,
            FinancialSubjectModel.cooperative_id == cooperative_id,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if model:
            await self.session.delete(model)
            await self.session.commit()


class BalanceRepository(IBalanceRepository):
    """SQLAlchemy implementation of Balance repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def calculate_balance(self, financial_subject_id: UUID) -> Balance | None:
        """Calculate balance for a financial subject.
        
        balance = total_accruals (applied) - total_payments (confirmed)
        """
        # Import models - will be updated when modules are migrated
        try:
            from app.modules.accruals.infrastructure.models import AccrualModel as Accrual
            from app.modules.payments.infrastructure.models import PaymentModel as Payment
        except ImportError:
            from app.models.accrual import Accrual
            from app.models.payment import Payment

        # Get financial subject
        result = await self.session.execute(
            select(FinancialSubjectModel).where(
                FinancialSubjectModel.id == financial_subject_id
            )
        )
        subject = result.scalar_one_or_none()
        if subject is None:
            return None

        # Sum of applied accruals
        accruals_result = await self.session.execute(
            select(func.sum(Accrual.amount)).where(
                Accrual.financial_subject_id == financial_subject_id,
                Accrual.status == "applied",
            )
        )
        total_accruals = accruals_result.scalar() or Decimal("0.00")

        # Sum of confirmed payments
        payments_result = await self.session.execute(
            select(func.sum(Payment.amount)).where(
                Payment.financial_subject_id == financial_subject_id,
                Payment.status == "confirmed",
            )
        )
        total_payments = payments_result.scalar() or Decimal("0.00")

        return Balance(
            financial_subject_id=financial_subject_id,
            subject_type=subject.subject_type,
            subject_id=subject.subject_id,
            cooperative_id=subject.cooperative_id,
            code=subject.code,
            total_accruals=total_accruals,
            total_payments=total_payments,
        )

    async def get_balances_by_cooperative(self, cooperative_id: UUID) -> list[Balance]:
        """Get balances for all financial subjects in cooperative."""
        try:
            from app.modules.accruals.infrastructure.models import AccrualModel as Accrual
            from app.modules.payments.infrastructure.models import PaymentModel as Payment
        except ImportError:
            from app.models.accrual import Accrual
            from app.models.payment import Payment

        # Get all financial subjects for cooperative
        result = await self.session.execute(
            select(FinancialSubjectModel).where(
                FinancialSubjectModel.cooperative_id == cooperative_id
            )
        )
        subjects = list(result.scalars().all())

        if not subjects:
            return []

        subject_ids = [s.id for s in subjects]

        # Sum of accruals by subject (applied)
        accruals_result = await self.session.execute(
            select(
                Accrual.financial_subject_id,
                func.sum(Accrual.amount).label("total"),
            )
            .where(
                Accrual.financial_subject_id.in_(subject_ids),
                Accrual.status == "applied",
            )
            .group_by(Accrual.financial_subject_id)
        )
        accruals_map = {row[0]: row[1] for row in accruals_result.all()}

        # Sum of payments by subject (confirmed)
        payments_result = await self.session.execute(
            select(
                Payment.financial_subject_id,
                func.sum(Payment.amount).label("total"),
            )
            .where(
                Payment.financial_subject_id.in_(subject_ids),
                Payment.status == "confirmed",
            )
            .group_by(Payment.financial_subject_id)
        )
        payments_map = {row[0]: row[1] for row in payments_result.all()}

        # Build result
        balances = []
        for subject in subjects:
            total_accruals = accruals_map.get(subject.id, Decimal("0.00"))
            total_payments = payments_map.get(subject.id, Decimal("0.00"))
            balances.append(
                Balance(
                    financial_subject_id=subject.id,
                    subject_type=subject.subject_type,
                    subject_id=subject.subject_id,
                    cooperative_id=subject.cooperative_id,
                    code=subject.code,
                    total_accruals=total_accruals,
                    total_payments=total_payments,
                )
            )

        return balances
