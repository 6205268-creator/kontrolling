"""Land Management domain repository interfaces.

Pure Python - no framework dependencies (FastAPI, SQLAlchemy, Pydantic).
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.shared.kernel.repositories import IRepository

from .entities import LandPlot, Owner, PlotOwnership


class ILandPlotRepository(IRepository[LandPlot], ABC):
    """Repository interface for LandPlot operations."""

    @abstractmethod
    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> LandPlot | None:
        """Get land plot by ID, filtered by cooperative."""
        pass

    @abstractmethod
    async def get_all(self, cooperative_id: UUID) -> list[LandPlot]:
        """Get all land plots for cooperative."""
        pass

    @abstractmethod
    async def get_by_plot_number(self, plot_number: str, cooperative_id: UUID) -> LandPlot | None:
        """Get land plot by plot number within cooperative."""
        pass

    @abstractmethod
    async def add(self, entity: LandPlot) -> LandPlot:
        """Add new land plot."""
        pass

    @abstractmethod
    async def update(self, entity: LandPlot) -> LandPlot:
        """Update existing land plot."""
        pass

    @abstractmethod
    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete land plot by ID."""
        pass


class IOwnerRepository(IRepository[Owner], ABC):
    """Repository interface for Owner operations."""

    @abstractmethod
    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> Owner | None:
        """Get owner by ID."""
        pass

    @abstractmethod
    async def get_all(self, cooperative_id: UUID) -> list[Owner]:
        """Get all owners."""
        pass

    @abstractmethod
    async def search_by_name_or_tax_id(self, query: str, limit: int = 100) -> list[Owner]:
        """Search owners by name or tax_id."""
        pass

    @abstractmethod
    async def add(self, entity: Owner) -> Owner:
        """Add new owner."""
        pass

    @abstractmethod
    async def update(self, entity: Owner) -> Owner:
        """Update existing owner."""
        pass

    @abstractmethod
    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete owner by ID."""
        pass


class IPlotOwnershipRepository(IRepository[PlotOwnership], ABC):
    """Repository interface for PlotOwnership operations."""

    @abstractmethod
    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> PlotOwnership | None:
        """Get plot ownership by ID."""
        pass

    @abstractmethod
    async def get_by_land_plot(self, land_plot_id: UUID, cooperative_id: UUID) -> list[PlotOwnership]:
        """Get all ownerships for a land plot."""
        pass

    @abstractmethod
    async def get_by_owner(self, owner_id: UUID, cooperative_id: UUID) -> list[PlotOwnership]:
        """Get all ownerships for an owner."""
        pass

    @abstractmethod
    async def get_current_ownerships(self, land_plot_id: UUID) -> list[PlotOwnership]:
        """Get current (non-closed) ownerships for a land plot."""
        pass

    @abstractmethod
    async def add(self, entity: PlotOwnership) -> PlotOwnership:
        """Add new plot ownership."""
        pass

    @abstractmethod
    async def update(self, entity: PlotOwnership) -> PlotOwnership:
        """Update existing plot ownership."""
        pass

    @abstractmethod
    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete plot ownership by ID."""
        pass
