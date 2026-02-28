"""Shared kernel - base abstractions for all modules."""

from .entities import BaseEntity
from .repositories import IRepository
from .exceptions import DomainError, ValidationError
from .events import DomainEvent, EventDispatcher

__all__ = [
    "BaseEntity",
    "IRepository",
    "DomainError",
    "ValidationError",
    "DomainEvent",
    "EventDispatcher",
]
