"""Payment Distribution application use cases.

Use cases for payment distribution module:
- CreditAccountUseCase: Credit payment to member's personal account
- DebitAccountUseCase: Debit from account to pay debt
- DistributePaymentUseCase: Distribute payment across debts by priority
"""

from datetime import UTC, datetime
from uuid import UUID

from app.modules.shared.kernel.events import EventDispatcher
from app.modules.shared.kernel.exceptions import ValidationError
from app.modules.shared.kernel.money import Money

from ..domain.entities import PaymentDistribution
from ..domain.events import PaymentDistributed, PaymentRefunded
from ..domain.repositories import (
    IMemberRepository,
    IPaymentDistributionRepository,
    IPersonalAccountRepository,
    IPersonalAccountTransactionRepository,
)


class CreditAccountUseCase:
    """Use case for crediting payment to member's personal account."""

    def __init__(
        self,
        member_repo: IMemberRepository,
        account_repo: IPersonalAccountRepository,
        transaction_repo: IPersonalAccountTransactionRepository,
        event_dispatcher: EventDispatcher | None = None,
    ):
        self.member_repo = member_repo
        self.account_repo = account_repo
        self.transaction_repo = transaction_repo
        self.event_dispatcher = event_dispatcher

    async def execute(
        self,
        payment_id: UUID,
        owner_id: UUID,
        cooperative_id: UUID,
        amount: Money,
        payment_date: datetime,
    ) -> None:
        """Credit payment to member's personal account.

        Args:
            payment_id: ID of the payment.
            owner_id: ID of the owner who made the payment.
            cooperative_id: ID of the cooperative.
            amount: Amount to credit.
            payment_date: Date of the payment.

        Raises:
            ValidationError: If member or account not found.
        """
        # Get or create member
        member = await self.member_repo.get_or_create_by_ownership(
            owner_id=owner_id,
            cooperative_id=cooperative_id,
        )

        # Get or create personal account
        account = await self.account_repo.get_by_member(member.id)
        if not account:
            # Create account if not exists
            account_number = f"PA-{cooperative_id.hex[:8]}-{member.id.hex[:8]}"
            account = await self.account_repo.create_for_member(
                member_id=member.id,
                cooperative_id=cooperative_id,
                account_number=account_number,
                opened_at=datetime.now(UTC),
            )

        # Credit the account
        account.credit(amount)
        await self.account_repo.update(account)

        # Create credit transaction
        transaction_number = f"CR-{payment_id.hex[:8]}"
        await self.transaction_repo.add_credit(
            account_id=account.id,
            payment_id=payment_id,
            transaction_number=transaction_number,
            transaction_date=payment_date,
            amount=amount,
            description=f"Зачисление платежа {payment_id}",
        )


class DebitAccountUseCase:
    """Use case for debiting from member's personal account."""

    def __init__(
        self,
        account_repo: IPersonalAccountRepository,
        transaction_repo: IPersonalAccountTransactionRepository,
    ):
        self.account_repo = account_repo
        self.transaction_repo = transaction_repo

    async def execute(
        self,
        account_id: UUID,
        distribution_id: UUID,
        amount: Money,
        transaction_date: datetime,
        description: str | None = None,
    ) -> None:
        """Debit from account for payment distribution.

        Args:
            account_id: ID of the personal account.
            distribution_id: ID of the payment distribution.
            amount: Amount to debit.
            transaction_date: Date of the transaction.
            description: Optional description.

        Raises:
            ValidationError: If insufficient balance.
        """
        # Get account
        account = await self.account_repo.get_by_id(account_id, UUID(int=0))
        if not account:
            raise ValidationError("Personal account not found")

        # Debit the account
        account.debit(amount)
        await self.account_repo.update(account)

        # Create debit transaction
        transaction_number = f"DB-{distribution_id.hex[:8]}"
        await self.transaction_repo.add_debit(
            account_id=account.id,
            distribution_id=distribution_id,
            transaction_number=transaction_number,
            transaction_date=transaction_date,
            amount=amount,
            description=description or f"Списание по распределению {distribution_id}",
        )


class DistributePaymentUseCase:
    """Use case for distributing payment across debts by priority."""

    def __init__(
        self,
        member_repo: IMemberRepository,
        account_repo: IPersonalAccountRepository,
        distribution_repo: IPaymentDistributionRepository,
        transaction_repo: IPersonalAccountTransactionRepository,
        debt_provider=None,  # Interface for getting debts
        event_dispatcher: EventDispatcher | None = None,
    ):
        self.member_repo = member_repo
        self.account_repo = account_repo
        self.distribution_repo = distribution_repo
        self.transaction_repo = transaction_repo
        self.debt_provider = debt_provider
        self.event_dispatcher = event_dispatcher

    async def execute(
        self,
        payment_id: UUID,
        owner_id: UUID,
        cooperative_id: UUID,
        payment_amount: Money,
        distributed_at: datetime | None = None,
    ) -> list[PaymentDistribution]:
        """Distribute payment across member's debts by priority.

        Algorithm:
        1. Get member's personal account
        2. Get available balance
        3. Get member's debts sorted by priority
        4. For each debt (highest priority first):
           - Calculate amount to distribute (min of remaining payment and debt)
           - Create PaymentDistribution
           - Create debit transaction
        5. Return list of distributions

        Args:
            payment_id: ID of the payment.
            owner_id: ID of the owner who made the payment.
            cooperative_id: ID of the cooperative.
            payment_amount: Total payment amount.
            distributed_at: Distribution datetime (defaults to now).

        Returns:
            List of created PaymentDistribution entities.

        Raises:
            ValidationError: If member or account not found.
        """
        if distributed_at is None:
            distributed_at = datetime.now(UTC)

        # Get member
        member = await self.member_repo.get_by_owner_and_cooperative(
            owner_id=owner_id,
            cooperative_id=cooperative_id,
        )
        if not member:
            raise ValidationError("Member not found")

        # Get personal account
        account = await self.account_repo.get_by_member(member.id)
        if not account:
            raise ValidationError("Personal account not found")

        # Get available balance
        available = account.balance
        if available.is_zero:
            return []

        # Get member's debts (from debt_provider)
        # TODO: Implement debt provider interface
        debts = []
        if self.debt_provider:
            debts = await self.debt_provider.get_member_debts(
                owner_id=owner_id,
                cooperative_id=cooperative_id,
            )

        # Distribute by priority
        distributions = []
        remaining = available

        for debt in sorted(debts, key=lambda d: d.priority):
            if remaining.is_zero:
                break

            # Calculate distribution amount
            distribute_amount = Money(
                min(remaining.amount, debt.balance.amount)
            )
            if distribute_amount.is_zero:
                continue

            # Create distribution
            distribution_number = f"PD-{payment_id.hex[:8]}-{len(distributions) + 1}"
            distribution = await self.distribution_repo.add_distribution(
                payment_id=payment_id,
                financial_subject_id=debt.financial_subject_id,
                accrual_id=debt.accrual_id,
                distribution_number=distribution_number,
                distributed_at=distributed_at,
                amount=distribute_amount,
                priority=debt.priority,
            )
            distributions.append(distribution)

            # Create debit transaction
            await self.transaction_repo.add_debit(
                account_id=account.id,
                distribution_id=distribution.id,
                transaction_number=f"DB-{distribution.id.hex[:8]}",
                transaction_date=distributed_at,
                amount=distribute_amount,
                description=f"Оплата {debt.description}",
            )

            # Update remaining
            remaining = Money(remaining.amount - distribute_amount.amount)

        # Publish events
        if self.event_dispatcher:
            for distribution in distributions:
                self.event_dispatcher.dispatch(
                    PaymentDistributed(
                        distribution_id=distribution.id,
                        payment_id=payment_id,
                        financial_subject_id=distribution.financial_subject_id,
                        amount=distribution.amount,
                    )
                )

        return distributions


class ReverseDistributionUseCase:
    """Use case for reversing payment distribution (when payment is cancelled)."""

    def __init__(
        self,
        distribution_repo: IPaymentDistributionRepository,
        account_repo: IPersonalAccountRepository,
        transaction_repo: IPersonalAccountTransactionRepository,
        event_dispatcher: EventDispatcher | None = None,
    ):
        self.distribution_repo = distribution_repo
        self.account_repo = account_repo
        self.transaction_repo = transaction_repo
        self.event_dispatcher = event_dispatcher

    async def execute(
        self,
        distribution_id: UUID,
        reversed_at: datetime | None = None,
    ) -> None:
        """Reverse a payment distribution.

        Args:
            distribution_id: ID of the distribution to reverse.
            reversed_at: Reversal datetime (defaults to now).

        Raises:
            ValidationError: If distribution not found or already reversed.
        """
        if reversed_at is None:
            reversed_at = datetime.now(UTC)

        # Get distribution
        distribution = await self.distribution_repo.get_by_id(distribution_id)
        if not distribution:
            raise ValidationError("Distribution not found")

        if distribution.status == "reversed":
            raise ValidationError("Distribution already reversed")

        # Reverse distribution
        distribution.reverse(reversed_at)
        await self.distribution_repo.update(distribution)

        # Credit back to account (create reverse transaction)
        # Note: This is simplified - in production you may want to link transactions
        account = await self.account_repo.get_by_member(UUID(int=0))  # TODO: Get member from distribution
        if account:
            transaction_number = f"RV-{distribution_id.hex[:8]}"
            await self.transaction_repo.add_credit(
                account_id=account.id,
                payment_id=None,
                transaction_number=transaction_number,
                transaction_date=reversed_at,
                amount=distribution.amount,
                description=f"Отмена распределения {distribution_id}",
            )

        # Publish event
        if self.event_dispatcher:
            self.event_dispatcher.dispatch(
                PaymentRefunded(
                    distribution_id=distribution_id,
                    amount=distribution.amount,
                )
            )
