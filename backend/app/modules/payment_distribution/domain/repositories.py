"""Payment Distribution repository interfaces."""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.modules.shared.kernel.money import Money
from app.modules.shared.kernel.repositories import IRepository

from .entities import Member, PaymentDistribution, PersonalAccount, PersonalAccountTransaction


class IMemberRepository(IRepository[Member], ABC):
    """Repository interface for Member operations."""

    @abstractmethod
    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> Member | None:
        """Get member by ID, filtered by cooperative."""
        pass

    @abstractmethod
    async def get_by_owner_and_cooperative(
        self,
        owner_id: UUID,
        cooperative_id: UUID,
    ) -> Member | None:
        """Get member by owner and cooperative."""
        pass

    @abstractmethod
    async def get_or_create_by_ownership(
        self,
        owner_id: UUID,
        cooperative_id: UUID,
    ) -> Member:
        """Get or create member when first PlotOwnership.is_primary is assigned.

        Args:
            owner_id: ID of the owner.
            cooperative_id: ID of the cooperative.

        Returns:
            Existing or newly created Member.
        """
        pass

    @abstractmethod
    async def get_members_by_cooperative(self, cooperative_id: UUID) -> list[Member]:
        """Get all members for cooperative."""
        pass


class IPersonalAccountRepository(IRepository[PersonalAccount], ABC):
    """Repository interface for PersonalAccount operations."""

    @abstractmethod
    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> PersonalAccount | None:
        """Get account by ID, filtered by cooperative."""
        pass

    @abstractmethod
    async def get_by_member(self, member_id: UUID) -> PersonalAccount | None:
        """Get account by member ID."""
        pass

    @abstractmethod
    async def get_by_account_number(self, account_number: str) -> PersonalAccount | None:
        """Get account by account number."""
        pass

    @abstractmethod
    async def create_for_member(
        self,
        member_id: UUID,
        cooperative_id: UUID,
        account_number: str,
        opened_at: datetime,
    ) -> PersonalAccount:
        """Create new personal account for member."""
        pass


class IPersonalAccountTransactionRepository(IRepository[PersonalAccountTransaction], ABC):
    """Repository interface for PersonalAccountTransaction operations."""

    @abstractmethod
    async def get_by_id(self, id: UUID) -> PersonalAccountTransaction | None:
        """Get transaction by ID."""
        pass

    @abstractmethod
    async def get_by_account(self, account_id: UUID) -> list[PersonalAccountTransaction]:
        """Get all transactions for account."""
        pass

    @abstractmethod
    async def get_by_payment(self, payment_id: UUID) -> list[PersonalAccountTransaction]:
        """Get all transactions for payment."""
        pass

    @abstractmethod
    async def add_credit(
        self,
        account_id: UUID,
        payment_id: UUID,
        transaction_number: str,
        transaction_date: datetime,
        amount: "Money",
        description: str | None = None,
    ) -> PersonalAccountTransaction:
        """Add credit transaction."""
        pass

    @abstractmethod
    async def add_debit(
        self,
        account_id: UUID,
        distribution_id: UUID,
        transaction_number: str,
        transaction_date: datetime,
        amount: "Money",
        description: str | None = None,
    ) -> PersonalAccountTransaction:
        """Add debit transaction."""
        pass


class IPaymentDistributionRepository(IRepository[PaymentDistribution], ABC):
    """Repository interface for PaymentDistribution operations."""

    @abstractmethod
    async def get_by_id(self, id: UUID) -> PaymentDistribution | None:
        """Get distribution by ID."""
        pass

    @abstractmethod
    async def get_by_payment(self, payment_id: UUID) -> list[PaymentDistribution]:
        """Get all distributions for payment."""
        pass

    @abstractmethod
    async def get_by_financial_subject(
        self,
        financial_subject_id: UUID,
    ) -> list[PaymentDistribution]:
        """Get all distributions for financial subject."""
        pass

    @abstractmethod
    async def add_distribution(
        self,
        payment_id: UUID,
        financial_subject_id: UUID,
        accrual_id: UUID | None,
        distribution_number: str,
        distributed_at: datetime,
        amount: "Money",
        priority: int,
    ) -> PaymentDistribution:
        """Add payment distribution."""
        pass
