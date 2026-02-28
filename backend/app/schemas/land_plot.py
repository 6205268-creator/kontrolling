from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.plot_ownership import PlotOwnershipCreate, PlotOwnershipInDB


class LandPlotBase(BaseModel):
    """Базовая схема LandPlot."""

    cooperative_id: UUID = Field(..., description="ID coopérative")
    plot_number: str = Field(..., description="Номер участка", min_length=1, max_length=50)
    area_sqm: Decimal = Field(..., description="Площадь в кв.м", gt=0)
    cadastral_number: str | None = Field(None, description="Кадастровый номер", max_length=50)
    status: str = Field("active", description="Статус", pattern="^(active|vacant|archived)$")


class LandPlotCreate(LandPlotBase):
    """Схема для создания LandPlot."""

    ownerships: list[PlotOwnershipCreate] = Field(
        default_factory=list, description="Список владельцев"
    )


class LandPlotUpdate(BaseModel):
    """Схема для обновления LandPlot."""

    plot_number: str | None = Field(None, description="Номер участка", min_length=1, max_length=50)
    area_sqm: Decimal | None = Field(None, description="Площадь в кв.м", gt=0)
    cadastral_number: str | None = Field(None, description="Кадастровый номер", max_length=50)
    status: str | None = Field(None, description="Статус", pattern="^(active|vacant|archived)$")


class LandPlotInDB(LandPlotBase):
    """Схема LandPlot с полями БД."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class LandPlotWithOwners(LandPlotInDB):
    """Схема LandPlot с владельцами и финансовым субъектом."""

    owners: list[PlotOwnershipInDB] = Field(default_factory=list, description="Список владельцев")
    financial_subject_id: UUID | None = Field(None, description="ID финансового субъекта")
    financial_subject_code: str | None = Field(None, description="Код финансового субъекта")


# Rebuild модель после всех определений
LandPlotWithOwners.model_rebuild()
