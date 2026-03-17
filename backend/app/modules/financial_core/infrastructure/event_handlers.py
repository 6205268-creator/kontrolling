"""Event handlers for financial_core module.

Subscribes to domain events from other modules and creates FinancialSubject automatically.
Also handles payment and accrual events for logging purposes.
"""

import logging
from typing import TYPE_CHECKING

from app.modules.shared.domain.events import LandPlotCreated, MeterCreated
from app.modules.shared.kernel.events import EventDispatcher

from ..domain.entities import FinancialSubject
from ..domain.repositories import IFinancialSubjectRepository

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# Import payment and accrual events for handler registration
# Import here to avoid circular imports at module level
def _get_payment_events():
    from app.modules.payments.domain.events import PaymentCancelled, PaymentConfirmed

    return PaymentConfirmed, PaymentCancelled


def _get_accrual_events():
    from app.modules.accruals.domain.events import AccrualApplied, AccrualCancelled

    return AccrualApplied, AccrualCancelled


class LandPlotCreatedHandler:
    """Handler for LandPlotCreated event.

    Creates FinancialSubject automatically when a new LandPlot is created.
    """

    def __init__(
        self,
        session_factory,
        fs_repo_class: type[IFinancialSubjectRepository],
    ):
        self.session_factory = session_factory
        self.fs_repo_class = fs_repo_class

    async def __call__(self, event: LandPlotCreated) -> None:
        """Handle LandPlotCreated event.

        Creates FinancialSubject with subject_type=LAND_PLOT.
        """
        async with self.session_factory() as session:
            repo = self.fs_repo_class(session)

            # Create FinancialSubject for the land plot
            import uuid

            from ..domain.entities import FinancialSubject

            fs = FinancialSubject(
                id=uuid.uuid4(),
                subject_type="LAND_PLOT",
                subject_id=event.land_plot_id,
                cooperative_id=event.cooperative_id,
                code=f"FS-LP-{event.plot_number}",
                status="active",
            )

            await repo.add(fs)
            await session.commit()


class MeterCreatedHandler:
    """Handler for MeterCreated event.

    Creates FinancialSubject automatically when a new Meter is created.
    """

    def __init__(
        self,
        session_factory,
        fs_repo_class: type[IFinancialSubjectRepository],
    ):
        self.session_factory = session_factory
        self.fs_repo_class = fs_repo_class

    async def __call__(self, event: MeterCreated) -> None:
        """Handle MeterCreated event.

        Creates FinancialSubject with subject_type={event.meter_type}_METER.
        """
        async with self.session_factory() as session:
            repo = self.fs_repo_class(session)

            # Create FinancialSubject for the meter
            import uuid

            subject_type = f"{event.meter_type}_METER"
            fs = FinancialSubject(
                id=uuid.uuid4(),
                subject_type=subject_type,
                subject_id=event.meter_id,
                cooperative_id=event.cooperative_id,
                code=f"FS-M-{event.serial_number}",
                status="active",
            )

            await repo.add(fs)
            await session.commit()


class PaymentConfirmedHandler:
    """Handler for PaymentConfirmed event.

    Logs payment confirmation for audit purposes.
    """

    def __call__(self, event) -> None:
        """Handle PaymentConfirmed event - log the payment."""
        logger.info(
            "Payment confirmed: id=%s, subject=%s, owner=%s, amount=%s, date=%s, op_number=%s",
            event.payment_id,
            event.financial_subject_id,
            event.payer_owner_id,
            event.amount,
            event.payment_date,
            event.operation_number,
        )


class PaymentCancelledHandler:
    """Handler for PaymentCancelled event.

    Logs payment cancellation for audit purposes.
    """

    def __call__(self, event) -> None:
        """Handle PaymentCancelled event - log the cancellation."""
        logger.info(
            "Payment cancelled: id=%s, cancelled_at=%s, by_user=%s, reason=%s",
            event.payment_id,
            event.cancelled_at,
            event.cancelled_by,
            event.reason or "N/A",
        )


class AccrualAppliedHandler:
    """Handler for AccrualApplied event.

    Logs accrual application for audit purposes.
    """

    def __call__(self, event) -> None:
        """Handle AccrualApplied event - log the application."""
        logger.info(
            "Accrual applied: id=%s, subject=%s, type=%s, amount=%s, date=%s, op_number=%s",
            event.accrual_id,
            event.financial_subject_id,
            event.contribution_type_id,
            event.amount,
            event.accrual_date,
            event.operation_number,
        )


class AccrualCancelledHandler:
    """Handler for AccrualCancelled event.

    Logs accrual cancellation for audit purposes.
    """

    def __call__(self, event) -> None:
        """Handle AccrualCancelled event - log the cancellation."""
        logger.info(
            "Accrual cancelled: id=%s, cancelled_at=%s, by_user=%s, reason=%s",
            event.accrual_id,
            event.cancelled_at,
            event.cancelled_by,
            event.reason or "N/A",
        )


def setup_event_handlers(
    event_dispatcher: EventDispatcher,
    session_factory,
    fs_repo_class: type[IFinancialSubjectRepository],
) -> None:
    """Setup event handlers for financial_core module.

    Args:
        event_dispatcher: Global event dispatcher instance.
        session_factory: AsyncSession factory for database access.
        fs_repo_class: FinancialSubjectRepository class.
    """
    # Register async handlers
    land_plot_handler = LandPlotCreatedHandler(session_factory, fs_repo_class)
    meter_handler = MeterCreatedHandler(session_factory, fs_repo_class)

    # Note: For async handlers, we need to wrap them or use an async event bus
    # For now, we register sync wrappers that schedule the async handlers

    def sync_land_plot_handler(event: LandPlotCreated) -> None:
        """Schedule async handler as task in the running event loop."""
        import asyncio as _asyncio

        _asyncio.create_task(land_plot_handler(event))

    def sync_meter_handler(event: MeterCreated) -> None:
        """Schedule async handler as task in the running event loop."""
        import asyncio as _asyncio

        _asyncio.create_task(meter_handler(event))

    event_dispatcher.register(LandPlotCreated, sync_land_plot_handler)
    event_dispatcher.register(MeterCreated, sync_meter_handler)

    # Register payment and accrual event handlers (logging)
    PaymentConfirmed, PaymentCancelled = _get_payment_events()
    AccrualApplied, AccrualCancelled = _get_accrual_events()

    event_dispatcher.register(PaymentConfirmed, PaymentConfirmedHandler())
    event_dispatcher.register(PaymentCancelled, PaymentCancelledHandler())
    event_dispatcher.register(AccrualApplied, AccrualAppliedHandler())
    event_dispatcher.register(AccrualCancelled, AccrualCancelledHandler())
