"""Event handlers for financial_core module.

Subscribes to domain events from other modules and creates FinancialSubject automatically.
"""

import asyncio
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.shared.kernel.events import EventDispatcher

from ..domain.events import LandPlotCreated, MeterCreated
from ..domain.repositories import IFinancialSubjectRepository

if TYPE_CHECKING:
    from ..application.use_cases import CreateFinancialSubjectUseCase


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
            from ..domain.entities import FinancialSubject
            import uuid
            
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
        """Synchronous wrapper for async handler."""
        asyncio.get_event_loop().run_until_complete(land_plot_handler(event))
    
    def sync_meter_handler(event: MeterCreated) -> None:
        """Synchronous wrapper for async handler."""
        asyncio.get_event_loop().run_until_complete(meter_handler(event))
    
    event_dispatcher.register(LandPlotCreated, sync_land_plot_handler)
    event_dispatcher.register(MeterCreated, sync_meter_handler)
