"""Cross-module domain events.

Events that are published by one module and consumed by another
live here to ensure a single canonical definition.

Module-specific events (consumed only within the same module) stay
in the respective module's domain/events.py.
"""

from dataclasses import dataclass
from uuid import UUID

from app.modules.shared.kernel.events import DomainEvent


@dataclass
class LandPlotCreated(DomainEvent):
    """Published by land_management when a new LandPlot is created.

    Consumed by financial_core to auto-create FinancialSubject.
    """

    land_plot_id: UUID
    cooperative_id: UUID
    plot_number: str
    area_sqm: float


@dataclass
class MeterCreated(DomainEvent):
    """Published by meters when a new Meter is created.

    Consumed by financial_core to auto-create FinancialSubject.
    """

    meter_id: UUID
    cooperative_id: UUID
    meter_type: str
    serial_number: str
