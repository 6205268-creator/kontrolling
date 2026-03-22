"""Обработчики событий для синхронизации DebtLine с начислениями и распределением платежей."""

import logging
import uuid
from typing import TYPE_CHECKING

from app.modules.shared.kernel.money import Money

if TYPE_CHECKING:
    from app.modules.accruals.domain.events import AccrualApplied, AccrualCancelled
    from app.modules.payment_distribution.domain.events import PaymentDistributed, PaymentRefunded

logger = logging.getLogger(__name__)


class DebtLineAccrualAppliedHandler:
    """Создаёт DebtLine при применении начисления (кроме типа PENALTY)."""

    def __init__(self, session_factory, debt_repo_class):
        self.session_factory = session_factory
        self.debt_repo_class = debt_repo_class

    async def __call__(self, event: "AccrualApplied") -> None:
        from datetime import UTC, datetime

        from sqlalchemy import select

        from app.modules.accruals.infrastructure.models import ContributionTypeModel

        async with self.session_factory() as session:
            ct_r = await session.execute(
                select(ContributionTypeModel).where(ContributionTypeModel.id == event.contribution_type_id)
            )
            ct = ct_r.scalar_one_or_none()
            if ct is not None and ct.code == "PENALTY":
                return

            repo = self.debt_repo_class(session)
            existing = await repo.get_by_accrual_id(event.accrual_id)
            if existing is not None:
                return

            from app.modules.financial_core.domain.entities import DebtLine

            now = datetime.now(UTC)
            line = DebtLine.from_accrual_applied(
                cooperative_id=event.cooperative_id,
                accrual_id=event.accrual_id,
                financial_subject_id=event.financial_subject_id,
                contribution_type_id=event.contribution_type_id,
                amount=event.amount,
                due_date=event.due_date,
                created_at=now,
                line_id=uuid.uuid4(),
            )
            await repo.add(line)
            await session.commit()


class DebtLineAccrualCancelledHandler:
    """Помечает DebtLine как written_off при отмене начисления."""

    def __init__(self, session_factory, debt_repo_class):
        self.session_factory = session_factory
        self.debt_repo_class = debt_repo_class

    async def __call__(self, event: "AccrualCancelled") -> None:
        async with self.session_factory() as session:
            repo = self.debt_repo_class(session)
            line = await repo.get_by_accrual_id(event.accrual_id)
            if line is None:
                return
            line.mark_written_off()
            await repo.update(line)
            await session.commit()


class DebtLinePaymentDistributedHandler:
    """Увеличивает paid_amount по строке долга при распределении платежа на начисление."""

    def __init__(self, session_factory, debt_repo_class):
        self.session_factory = session_factory
        self.debt_repo_class = debt_repo_class

    async def __call__(self, event: "PaymentDistributed") -> None:
        if event.accrual_id is None:
            return
        async with self.session_factory() as session:
            repo = self.debt_repo_class(session)
            line = await repo.get_by_accrual_id(event.accrual_id)
            if line is None:
                return
            line.apply_payment(Money(event.amount))
            await repo.update(line)
            await session.commit()


class DebtLinePaymentRefundedHandler:
    """Уменьшает paid_amount при отмене распределения."""

    def __init__(self, session_factory, debt_repo_class):
        self.session_factory = session_factory
        self.debt_repo_class = debt_repo_class

    async def __call__(self, event: "PaymentRefunded") -> None:
        if event.accrual_id is None:
            return
        async with self.session_factory() as session:
            repo = self.debt_repo_class(session)
            line = await repo.get_by_accrual_id(event.accrual_id)
            if line is None:
                return
            line.reverse_payment(Money(event.amount))
            await repo.update(line)
            await session.commit()
