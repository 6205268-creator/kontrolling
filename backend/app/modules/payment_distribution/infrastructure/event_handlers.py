"""Event handlers for payment_distribution module.

Subscribes to PaymentConfirmed event and automatically:
1. Credits payment to member's personal account
2. Distributes payment across debts by priority
"""

import logging
from typing import TYPE_CHECKING

from app.modules.shared.kernel.events import EventDispatcher

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class PaymentConfirmedHandler:
    """Handler for PaymentConfirmed event.

    Automatically credits payment to member's personal account
    and distributes it across debts by priority.
    """

    def __init__(
        self,
        session_factory,
        credit_account_use_case_class,
        distribute_payment_use_case_class,
        member_repo_class,
    ):
        self.session_factory = session_factory
        self.credit_account_use_case_class = credit_account_use_case_class
        self.distribute_payment_use_case_class = distribute_payment_use_case_class
        self.member_repo_class = member_repo_class

    async def __call__(self, event) -> None:
        """Handle PaymentConfirmed event.

        1. Get member by owner_id and cooperative_id
        2. Credit payment to member's personal account
        3. Distribute payment across debts by priority
        """
        from app.modules.payment_distribution.infrastructure.repositories import (
            PaymentDistributionRepository,
            PersonalAccountRepository,
            PersonalAccountTransactionRepository,
        )
        from app.modules.shared.kernel.money import Money

        async with self.session_factory() as session:
            # Get member repository
            member_repo = self.member_repo_class(session)

            # Get member (or create if not exists)
            member = await member_repo.get_or_create_by_ownership(
                owner_id=event.payer_owner_id,
                cooperative_id=event.cooperative_id,
            )

            account_repo = PersonalAccountRepository(session)
            transaction_repo = PersonalAccountTransactionRepository(session)

            credit_use_case = self.credit_account_use_case_class(
                member_repo=member_repo,
                account_repo=account_repo,
                transaction_repo=transaction_repo,
            )

            # Credit the payment to account
            await credit_use_case.execute(
                payment_id=event.payment_id,
                owner_id=event.payer_owner_id,
                cooperative_id=event.cooperative_id,
                amount=Money(event.amount),
                payment_date=event.payment_date,
            )

            logger.info(
                "Payment credited to account: payment_id=%s, member_id=%s, amount=%s",
                event.payment_id,
                member.id,
                event.amount,
            )

            # Distribute payment use case
            distribution_repo = PaymentDistributionRepository(session)

            distribute_use_case = self.distribute_payment_use_case_class(
                member_repo=member_repo,
                account_repo=account_repo,
                distribution_repo=distribution_repo,
                transaction_repo=transaction_repo,
                debt_provider=None,  # TODO: Implement debt provider
            )

            # Distribute payment across debts
            distributions = await distribute_use_case.execute(
                payment_id=event.payment_id,
                owner_id=event.payer_owner_id,
                cooperative_id=event.cooperative_id,
                payment_amount=Money(event.amount),
                distributed_at=event.payment_date,
            )

            if distributions:
                logger.info(
                    "Payment distributed: payment_id=%s, distributions=%d, total=%s",
                    event.payment_id,
                    len(distributions),
                    sum(d.amount.amount for d in distributions),
                )
            else:
                logger.info(
                    "Payment credited but not distributed (no debts): payment_id=%s",
                    event.payment_id,
                )


def setup_payment_distribution_handlers(
    event_dispatcher: EventDispatcher,
    session_factory,
) -> None:
    """Setup event handlers for payment_distribution module.

    Args:
        event_dispatcher: Global event dispatcher instance.
        session_factory: AsyncSession factory for database access.
    """
    from app.modules.payment_distribution.application.use_cases import (
        CreditAccountUseCase,
        DistributePaymentUseCase,
    )
    from app.modules.payment_distribution.infrastructure.repositories import (
        MemberRepository,
    )

    # Import PaymentConfirmed event
    from app.modules.payments.domain.events import PaymentConfirmed

    # Create handler
    handler = PaymentConfirmedHandler(
        session_factory=session_factory,
        credit_account_use_case_class=CreditAccountUseCase,
        distribute_payment_use_case_class=DistributePaymentUseCase,
        member_repo_class=MemberRepository,
    )

    # Register handler
    def sync_handler(event) -> None:
        """Schedule async handler as task in the running event loop."""
        import asyncio

        asyncio.create_task(handler(event))

    event_dispatcher.register(PaymentConfirmed, sync_handler)
