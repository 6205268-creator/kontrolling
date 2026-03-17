"""Domain events for meters module.

Pure Python - no framework dependencies.
"""

from dataclasses import dataclass
from uuid import UUID

from app.modules.shared.domain.events import MeterCreated as MeterCreated
from app.modules.shared.kernel.events import DomainEvent


@dataclass
class MeterReadingAdded(DomainEvent):
    """Event published when a meter reading is added."""

    reading_id: UUID
    meter_id: UUID
    reading_value: float
    reading_date: str  # ISO format date
