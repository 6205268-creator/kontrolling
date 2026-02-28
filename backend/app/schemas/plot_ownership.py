from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PlotOwnershipBase(BaseModel):
    """Базовая схема PlotOwnership."""

    owner_id: UUID = Field(..., description="ID владельца")
    share_numerator: int = Field(..., description="Числитель доли", ge=1)
    share_denominator: int = Field(..., description="Знаменатель доли", ge=1)
    is_primary: bool = Field(False, description="Основной владелец (член СТ)")
    valid_from: date = Field(..., description="Дата начала владения")
    valid_to: date | None = Field(None, description="Дата окончания владения")


class PlotOwnershipCreate(PlotOwnershipBase):
    """Схема для создания PlotOwnership."""

    land_plot_id: UUID | None = Field(
        None, description="ID земельного участка (устанавливается сервисом)"
    )


class PlotOwnershipUpdate(BaseModel):
    """Схема для обновления PlotOwnership."""

    share_numerator: int | None = Field(None, description="Числитель доли", ge=1)
    share_denominator: int | None = Field(None, description="Знаменатель доли", ge=1)
    is_primary: bool | None = Field(None, description="Основной владелец (член СТ)")
    valid_to: date | None = Field(None, description="Дата окончания владения")


class PlotOwnershipInDB(PlotOwnershipBase):
    """Схема PlotOwnership с полями БД."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    land_plot_id: UUID
    created_at: datetime
    updated_at: datetime
