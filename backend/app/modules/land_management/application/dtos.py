"""DTOs for land_management application layer."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OwnerBase(BaseModel):
    """Base schema for Owner."""

    owner_type: str = Field(..., description="Тип владельца", pattern="^(physical|legal)$")
    name: str = Field(..., description="ФИО или название организации", min_length=1, max_length=255)
    tax_id: str | None = Field(None, description="УНП/ИД", max_length=20)
    contact_phone: str | None = Field(None, description="Телефон", max_length=50)
    contact_email: str | None = Field(None, description="Email", max_length=255)


class OwnerCreate(OwnerBase):
    """Schema for creating an Owner."""

    pass


class OwnerUpdate(BaseModel):
    """Schema for updating an Owner."""

    owner_type: str | None = Field(None, description="Тип владельца", pattern="^(physical|legal)$")
    name: str | None = Field(
        None, description="ФИО или название организации", min_length=1, max_length=255
    )
    tax_id: str | None = Field(None, description="УНП/ИД", max_length=20)
    contact_phone: str | None = Field(None, description="Телефон", max_length=50)
    contact_email: str | None = Field(None, description="Email", max_length=255)


class OwnerInDB(OwnerBase):
    """Schema for Owner with DB fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class LandPlotBase(BaseModel):
    """Base schema for LandPlot."""

    cooperative_id: UUID = Field(..., description="ID товарищества")
    plot_number: str = Field(..., description="Номер участка", min_length=1, max_length=50)
    area_sqm: Decimal = Field(..., description="Площадь в кв.м", gt=0)
    cadastral_number: str | None = Field(None, description="Кадастровый номер", max_length=50)
    status: str = Field("active", description="Статус", pattern="^(active|vacant|archived)$")


class LandPlotCreate(LandPlotBase):
    """Schema for creating a LandPlot."""

    ownerships: list["PlotOwnershipCreate"] = Field(
        default_factory=list, description="Список владельцев"
    )


class LandPlotUpdate(BaseModel):
    """Schema for updating a LandPlot."""

    plot_number: str | None = Field(None, description="Номер участка", min_length=1, max_length=50)
    area_sqm: Decimal | None = Field(None, description="Площадь в кв.м", gt=0)
    cadastral_number: str | None = Field(None, description="Кадастровый номер", max_length=50)
    status: str | None = Field(None, description="Статус", pattern="^(active|vacant|archived)$")
    ownerships: list["PlotOwnershipCreate"] | None = Field(
        None,
        description="Полный список владельцев (текущие закрываются с valid_to=сегодня, затем создаются переданные)",
    )


class LandPlotInDB(LandPlotBase):
    """Schema for LandPlot with DB fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class PlotOwnershipBase(BaseModel):
    """Base schema for PlotOwnership."""

    owner_id: UUID = Field(..., description="ID владельца")
    share_numerator: int = Field(..., description="Числитель доли", ge=1)
    share_denominator: int = Field(..., description="Знаменатель доли", ge=1)
    is_primary: bool = Field(False, description="Основной владелец (член СТ)")
    valid_from: date = Field(..., description="Дата начала владения")
    valid_to: date | None = Field(None, description="Дата окончания владения")


class PlotOwnershipCreate(PlotOwnershipBase):
    """Schema for creating a PlotOwnership."""

    land_plot_id: UUID | None = Field(
        None, description="ID земельного участка (устанавливается сервисом)"
    )


class PlotOwnershipUpdate(BaseModel):
    """Schema for updating a PlotOwnership."""

    share_numerator: int | None = Field(None, description="Числитель доли", ge=1)
    share_denominator: int | None = Field(None, description="Знаменатель доли", ge=1)
    is_primary: bool | None = Field(None, description="Основной владелец (член СТ)")
    valid_to: date | None = Field(None, description="Дата окончания владения")


class PlotOwnershipInDB(PlotOwnershipBase):
    """Schema for PlotOwnership with DB fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    land_plot_id: UUID
    created_at: datetime
    updated_at: datetime


class LandPlotWithOwners(LandPlotInDB):
    """Schema for LandPlot with owners and financial subject."""

    owners: list[PlotOwnershipInDB] = Field(default_factory=list, description="Список владельцев")
    financial_subject_id: UUID | None = Field(None, description="ID финансового субъекта")
    financial_subject_code: str | None = Field(None, description="Код финансового субъекта")
