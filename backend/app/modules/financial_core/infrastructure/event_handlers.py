"""Event handlers for financial_core module.

Subscribes to domain events from other modules.
"""

from app.modules.shared.kernel.events import EventDispatcher

from ..application.use_cases import CreateFinancialSubjectUseCase, LandPlotCreatedHandler
from ..domain.events import LandPlotCreated, MeterCreated
from .repositories import FinancialSubjectRepository


def setup_event_handlers(event_dispatcher: EventDispatcher, session_factory) -> None:
    """Setup event handlers for financial_core module.
    
    Args:
        event_dispatcher: Global event dispatcher instance.
        session_factory: AsyncSession factory for database access.
    """
    # Handlers will be registered here as async event bus is implemented
    # For now, events are handled synchronously in use cases
    pass
