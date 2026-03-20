"""Payment Distribution repository implementations.

SQLAlchemy implementation of payment distribution repositories.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.payment_distribution.domain.entities import (
    Member,
    PaymentDistribution,
    PersonalAccount,
    PersonalAccountTransaction,
)
from app.modules.payment_distribution.domain.repositories import (
    IMemberRepository,
    IPaymentDistributionRepository,
    IPersonalAccountRepository,
    IPersonalAccountTransactionRepository,
)
from app.modules.shared.kernel.money import Money

from .models import (
    MemberModel,
    PaymentDistributionModel,
    PersonalAccountModel,
    PersonalAccountTransactionModel,
)


class MemberRepository(IMemberRepository):
    """SQLAlchemy implementation of Member repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> Member | None:
        """Get member by ID, filtered by cooperative."""
        query = select(MemberModel).where(
            MemberModel.id == id,
            MemberModel.cooperative_id == cooperative_id,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_owner_and_cooperative(
        self,
        owner_id: UUID,
        cooperative_id: UUID,
    ) -> Member | None:
        """Get member by owner and cooperative."""
        query = select(MemberModel).where(
            MemberModel.owner_id == owner_id,
            MemberModel.cooperative_id == cooperative_id,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_or_create_by_ownership(
        self,
        owner_id: UUID,
        cooperative_id: UUID,
    ) -> Member:
        """Get or create member when first PlotOwnership.is_primary is assigned."""
        # Try to get existing member
        member = await self.get_by_owner_and_cooperative(owner_id, cooperative_id)
        if member:
            return member

        # Create new member
        from datetime import datetime

        member = Member(
            owner_id=owner_id,
            cooperative_id=cooperative_id,
            status="active",
            joined_at=datetime.now(UTC),
        )
        model = MemberModel.from_domain(member)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def get_members_by_cooperative(self, cooperative_id: UUID) -> list[Member]:
        """Get all members for cooperative."""
        query = select(MemberModel).where(MemberModel.cooperative_id == cooperative_id)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def add(self, entity: Member) -> Member:
        """Add new member."""
        model = MemberModel.from_domain(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def update(self, entity: Member) -> Member:
        """Update existing member."""
        query = select(MemberModel).where(MemberModel.id == entity.id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(f"Member with id {entity.id} not found")

        model.status = entity.status
        model.personal_account_id = entity.personal_account_id
        model.joined_at = entity.joined_at

        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete member by ID."""
        query = select(MemberModel).where(
            MemberModel.id == id,
            MemberModel.cooperative_id == cooperative_id,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.commit()


class PersonalAccountRepository(IPersonalAccountRepository):
    """SQLAlchemy implementation of PersonalAccount repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> PersonalAccount | None:
        """Get account by ID, filtered by cooperative."""
        query = select(PersonalAccountModel).where(
            PersonalAccountModel.id == id,
            PersonalAccountModel.cooperative_id == cooperative_id,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_member(self, member_id: UUID) -> PersonalAccount | None:
        """Get account by member ID."""
        query = select(PersonalAccountModel).where(
            PersonalAccountModel.member_id == member_id
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_account_number(self, account_number: str) -> PersonalAccount | None:
        """Get account by account number."""
        query = select(PersonalAccountModel).where(
            PersonalAccountModel.account_number == account_number
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def create_for_member(
        self,
        member_id: UUID,
        cooperative_id: UUID,
        account_number: str,
        opened_at: datetime,
    ) -> PersonalAccount:
        """Create new personal account for member."""
        account = PersonalAccount(
            member_id=member_id,
            cooperative_id=cooperative_id,
            account_number=account_number,
            balance=Money.zero(),
            status="active",
            opened_at=opened_at,
        )
        model = PersonalAccountModel.from_domain(account)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def update(self, entity: PersonalAccount) -> PersonalAccount:
        """Update existing account."""
        query = select(PersonalAccountModel).where(PersonalAccountModel.id == entity.id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(f"PersonalAccount with id {entity.id} not found")

        model.balance = entity.balance.amount
        model.status = entity.status
        model.closed_at = entity.closed_at

        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def add(self, entity: PersonalAccount) -> PersonalAccount:
        """Add new account (alias for create_for_member)."""
        model = PersonalAccountModel.from_domain(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete account by ID."""
        query = select(PersonalAccountModel).where(
            PersonalAccountModel.id == id,
            PersonalAccountModel.cooperative_id == cooperative_id,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.commit()


class PersonalAccountTransactionRepository(IPersonalAccountTransactionRepository):
    """SQLAlchemy implementation of PersonalAccountTransaction repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> PersonalAccountTransaction | None:
        """Get transaction by ID."""
        query = select(PersonalAccountTransactionModel).where(
            PersonalAccountTransactionModel.id == id
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_account(self, account_id: UUID) -> list[PersonalAccountTransaction]:
        """Get all transactions for account."""
        query = select(PersonalAccountTransactionModel).where(
            PersonalAccountTransactionModel.account_id == account_id
        ).order_by(PersonalAccountTransactionModel.transaction_date.desc())
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def get_by_payment(self, payment_id: UUID) -> list[PersonalAccountTransaction]:
        """Get all transactions for payment."""
        query = select(PersonalAccountTransactionModel).where(
            PersonalAccountTransactionModel.payment_id == payment_id
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def add_credit(
        self,
        account_id: UUID,
        payment_id: UUID,
        transaction_number: str,
        transaction_date: datetime,
        amount: Money,
        description: str | None = None,
    ) -> PersonalAccountTransaction:
        """Add credit transaction."""
        transaction = PersonalAccountTransaction(
            account_id=account_id,
            payment_id=payment_id,
            transaction_number=transaction_number,
            transaction_date=transaction_date,
            amount=amount,
            type="credit",
            description=description,
        )
        model = PersonalAccountTransactionModel.from_domain(transaction)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def add_debit(
        self,
        account_id: UUID,
        distribution_id: UUID,
        transaction_number: str,
        transaction_date: datetime,
        amount: Money,
        description: str | None = None,
    ) -> PersonalAccountTransaction:
        """Add debit transaction."""
        transaction = PersonalAccountTransaction(
            account_id=account_id,
            distribution_id=distribution_id,
            transaction_number=transaction_number,
            transaction_date=transaction_date,
            amount=amount,
            type="debit",
            description=description,
        )
        model = PersonalAccountTransactionModel.from_domain(transaction)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def add(self, entity: PersonalAccountTransaction) -> PersonalAccountTransaction:
        """Add new transaction."""
        model = PersonalAccountTransactionModel.from_domain(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def update(self, entity: PersonalAccountTransaction) -> PersonalAccountTransaction:
        """Update existing transaction."""
        query = select(PersonalAccountTransactionModel).where(
            PersonalAccountTransactionModel.id == entity.id
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(f"Transaction with id {entity.id} not found")

        model.type = entity.type
        model.description = entity.description

        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete transaction by ID (not typically used for audit reasons)."""
        query = select(PersonalAccountTransactionModel).where(
            PersonalAccountTransactionModel.id == id
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.commit()


class PaymentDistributionRepository(IPaymentDistributionRepository):
    """SQLAlchemy implementation of PaymentDistribution repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> PaymentDistribution | None:
        """Get distribution by ID."""
        query = select(PaymentDistributionModel).where(
            PaymentDistributionModel.id == id
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_payment(self, payment_id: UUID) -> list[PaymentDistribution]:
        """Get all distributions for payment."""
        query = select(PaymentDistributionModel).where(
            PaymentDistributionModel.payment_id == payment_id
        ).order_by(PaymentDistributionModel.priority)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def get_by_financial_subject(
        self,
        financial_subject_id: UUID,
    ) -> list[PaymentDistribution]:
        """Get all distributions for financial subject."""
        query = select(PaymentDistributionModel).where(
            PaymentDistributionModel.financial_subject_id == financial_subject_id
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def add_distribution(
        self,
        payment_id: UUID,
        financial_subject_id: UUID,
        accrual_id: UUID | None,
        distribution_number: str,
        distributed_at: datetime,
        amount: Money,
        priority: int,
    ) -> PaymentDistribution:
        """Add payment distribution."""
        distribution = PaymentDistribution(
            payment_id=payment_id,
            financial_subject_id=financial_subject_id,
            accrual_id=accrual_id,
            distribution_number=distribution_number,
            distributed_at=distributed_at,
            amount=amount,
            priority=priority,
            status="applied",
        )
        model = PaymentDistributionModel.from_domain(distribution)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def add(self, entity: PaymentDistribution) -> PaymentDistribution:
        """Add new distribution."""
        model = PaymentDistributionModel.from_domain(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def update(self, entity: PaymentDistribution) -> PaymentDistribution:
        """Update existing distribution."""
        query = select(PaymentDistributionModel).where(
            PaymentDistributionModel.id == entity.id
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(f"PaymentDistribution with id {entity.id} not found")

        model.status = entity.status

        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete distribution by ID (not typically used for audit reasons)."""
        query = select(PaymentDistributionModel).where(
            PaymentDistributionModel.id == id
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.commit()
