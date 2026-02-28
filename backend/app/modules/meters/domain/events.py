"""Domain events for meters module.

Pure Python - no framework dependencies.
"""

from dataclasses import dataclass
from uuid import UUID

from app.modules.shared.kernel.events import DomainEvent


@dataclass
class MeterCreated(DomainEvent):
    """Event published when a new Meter is created.

    Used by financial_core to create FinancialSubject automatically.
    """

    meter_id: UUID
    cooperative_id: UUID
    meter_type: str  # WATER_METER or ELECTRICITY_METER
    serial_number: str


@dataclass
class MeterReadingAdded(DomainEvent):
    """Event published when a meter reading is added."""

    reading_id: UUID
    meter_id: UUID
    reading_value: float
    reading_date: str  # ISO format date
