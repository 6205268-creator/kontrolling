"""Domain events base classes and dispatcher.

Pure Python - no framework dependencies (FastAPI, SQLAlchemy, Pydantic).
"""

from abc import ABC
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Callable, Dict, List, Type
from uuid import UUID, uuid4


@dataclass(kw_only=True)
class DomainEvent(ABC):
    """Base class for all domain events.

    Domain events represent something meaningful that happened in the domain.
    They are used for inter-module communication without direct dependencies.
    """

    event_id: UUID = field(default_factory=uuid4)
    occurred_on: datetime = field(default_factory=lambda: datetime.now(UTC))


class EventDispatcher:
    """In-process event dispatcher for domain events.

    Handlers are called synchronously. For async operations or
    cross-service events, use an event bus with message queue.
    """

    _handlers: Dict[Type[DomainEvent], List[Callable[[DomainEvent], None]]] = {}

    @classmethod
    def register(
        cls, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]
    ) -> None:
        """Register a handler for an event type.

        Args:
            event_type: The domain event class to handle.
            handler: Callable that accepts the event as argument.
        """
        cls._handlers.setdefault(event_type, []).append(handler)

    @classmethod
    def dispatch(cls, event: DomainEvent) -> None:
        """Dispatch an event to all registered handlers.

        Args:
            event: The domain event to dispatch.
        """
        handlers = cls._handlers.get(type(event), [])
        for handler in handlers:
            handler(event)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered handlers. Useful for testing."""
        cls._handlers.clear()
