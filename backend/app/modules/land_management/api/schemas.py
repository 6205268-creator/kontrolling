"""Pydantic schemas for land_management API."""

from app.modules.land_management.application.dtos import (
    LandPlotBase,
    LandPlotCreate,
    LandPlotInDB,
    LandPlotUpdate,
    LandPlotWithOwners,
    OwnerBase,
    OwnerCreate,
    OwnerInDB,
    OwnerUpdate,
    PlotOwnershipBase,
    PlotOwnershipCreate,
    PlotOwnershipInDB,
    PlotOwnershipUpdate,
)

__all__ = [
    "LandPlotBase",
    "LandPlotCreate",
    "LandPlotInDB",
    "LandPlotUpdate",
    "LandPlotWithOwners",
    "OwnerBase",
    "OwnerCreate",
    "OwnerInDB",
    "OwnerUpdate",
    "PlotOwnershipBase",
    "PlotOwnershipCreate",
    "PlotOwnershipInDB",
    "PlotOwnershipUpdate",
]
