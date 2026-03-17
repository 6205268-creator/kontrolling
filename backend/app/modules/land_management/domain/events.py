"""Domain events for land_management module.

Pure Python - no framework dependencies.
"""

from dataclasses import dataclass
from uuid import UUID

from app.modules.shared.domain.events import LandPlotCreated as LandPlotCreated
from app.modules.shared.kernel.events import DomainEvent


@dataclass
class OwnerCreated(DomainEvent):
    """Event published when a new Owner is created."""

    owner_id: UUID
    owner_type: str
    name: str


@dataclass
class PlotOwnershipCreated(DomainEvent):
    """Event published when PlotOwnership is created."""

    ownership_id: UUID
    land_plot_id: UUID
    owner_id: UUID
    share_numerator: int
    share_denominator: int
    is_primary: bool


@dataclass
class PlotOwnershipTransferred(DomainEvent):
    """Event published when PlotOwnership is closed/transferred."""

    ownership_id: UUID
    land_plot_id: UUID
    previous_owner_id: UUID
    valid_to: str  # ISO format date
