"""Financial Core repository implementations.

SQLAlchemy implementation of financial core repositories.
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.financial_core.domain.entities import Balance, FinancialSubject
from app.modules.financial_core.domain.repositories import (
    IBalanceRepository,
    IFinancialSubjectRepository,
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
    """SQLAlchemy implementation of Balance repository.
    
    Implements balance calculation as of a specific date (as_of_date).
    
    Rule: Operation participates in balance on date X if and only if:
    1. event_date <= X (accrual_date for Accrual, payment_date for Payment)
    2. date(created_at) <= X
    3. status is correct (applied for Accrual, confirmed for Payment)
    4. NOT cancelled OR (cancelled AND cancelled_at > X)
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def calculate_balance(
        self,
        financial_subject_id: UUID,
        as_of_date: date | None = None,
    ) -> Balance | None:
        """Calculate balance for a financial subject as of a specific date.
        
        balance = total_accruals (applied) - total_payments (confirmed)
        
        Args:
            financial_subject_id: ID of financial subject.
            as_of_date: Date to calculate balance for. If None, uses today's date.
            
        Returns:
            Balance object or None if subject not found.
        """
        # Use today's date if not specified
        if as_of_date is None:
            as_of_date = date.today()

        # Import models from modules
        from app.modules.accruals.infrastructure.models import AccrualModel as Accrual
        from app.modules.payments.infrastructure.models import PaymentModel as Payment

        # Get financial subject
        result = await self.session.execute(
            select(FinancialSubjectModel).where(
                FinancialSubjectModel.id == financial_subject_id
            )
        )
        subject = result.scalar_one_or_none()
        if subject is None:
            return None

        # Build conditions for accruals
        # 1. accrual_date <= as_of_date
        # 2. status == 'applied'
        # 3. (status != 'cancelled') OR (cancelled_at IS NOT NULL AND cancelled_at > as_of_date)
        accrual_conditions = [
            Accrual.financial_subject_id == financial_subject_id,
            Accrual.accrual_date <= as_of_date,
            Accrual.status == "applied",
        ]
        # Not cancelled OR cancelled after as_of_date
        # Use func.date() to convert cancelled_at (datetime) to date for comparison
        accrual_not_cancelled_condition = (
            (Accrual.status != "cancelled") |
            ((Accrual.cancelled_at.isnot(None)) & (func.date(Accrual.cancelled_at) > as_of_date))
        )
        accrual_conditions.append(accrual_not_cancelled_condition)

        # Sum of applied accruals
        accruals_result = await self.session.execute(
            select(func.sum(Accrual.amount)).where(*accrual_conditions)
        )
        total_accruals = accruals_result.scalar() or Decimal("0.00")

        # Build conditions for payments
        # 1. payment_date <= as_of_date
        # 2. status == 'confirmed'
        # 3. (status != 'cancelled') OR (cancelled_at IS NOT NULL AND cancelled_at > as_of_date)
        payment_conditions = [
            Payment.financial_subject_id == financial_subject_id,
            Payment.payment_date <= as_of_date,
            Payment.status == "confirmed",
        ]
        # Not cancelled OR cancelled after as_of_date
        payment_not_cancelled_condition = (
            (Payment.status != "cancelled") |
            ((Payment.cancelled_at.isnot(None)) & (func.date(Payment.cancelled_at) > as_of_date))
        )
        payment_conditions.append(payment_not_cancelled_condition)

        # Sum of confirmed payments
        payments_result = await self.session.execute(
            select(func.sum(Payment.amount)).where(*payment_conditions)
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

    async def get_balances_by_cooperative(
        self,
        cooperative_id: UUID,
        as_of_date: date | None = None,
    ) -> list[Balance]:
        """Get balances for all financial subjects in cooperative as of a specific date.
        
        Args:
            cooperative_id: ID of cooperative.
            as_of_date: Date to calculate balances for. If None, uses today's date.
            
        Returns:
            List of Balance objects.
        """
        # Use today's date if not specified
        if as_of_date is None:
            as_of_date = date.today()

        # Import models from modules
        from app.modules.accruals.infrastructure.models import AccrualModel as Accrual
        from app.modules.payments.infrastructure.models import PaymentModel as Payment

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

        # Build conditions for accruals (same as calculate_balance but for multiple subjects)
        accrual_conditions = [
            Accrual.financial_subject_id.in_(subject_ids),
            Accrual.accrual_date <= as_of_date,
            Accrual.status == "applied",
            (Accrual.status != "cancelled") |
            ((Accrual.cancelled_at.isnot(None)) & (func.date(Accrual.cancelled_at) > as_of_date)),
        ]

        # Sum of accruals by subject (applied)
        accruals_result = await self.session.execute(
            select(
                Accrual.financial_subject_id,
                func.sum(Accrual.amount).label("total"),
            )
            .where(*accrual_conditions)
            .group_by(Accrual.financial_subject_id)
        )
        accruals_map = {row[0]: row[1] for row in accruals_result.all()}

        # Build conditions for payments
        payment_conditions = [
            Payment.financial_subject_id.in_(subject_ids),
            Payment.payment_date <= as_of_date,
            Payment.status == "confirmed",
            (Payment.status != "cancelled") |
            ((Payment.cancelled_at.isnot(None)) & (func.date(Payment.cancelled_at) > as_of_date)),
        ]

        # Sum of payments by subject (confirmed)
        payments_result = await self.session.execute(
            select(
                Payment.financial_subject_id,
                func.sum(Payment.amount).label("total"),
            )
            .where(*payment_conditions)
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
