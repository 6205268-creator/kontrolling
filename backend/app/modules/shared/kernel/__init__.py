"""Shared kernel - base abstractions for all modules."""

from .entities import BaseEntity
from .events import DomainEvent, EventDispatcher
from .exceptions import DomainError, ValidationError
from .repositories import IRepository

__all__ = [
    "BaseEntity",
    "IRepository",
    "DomainError",
    "ValidationError",
    "DomainEvent",
    "EventDispatcher",
]
