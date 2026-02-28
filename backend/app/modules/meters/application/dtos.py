"""DTOs for meters module."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MeterBase(BaseModel):
    """Base schema for Meter."""

    owner_id: UUID = Field(..., description="ID владельца")
    meter_type: str = Field(..., description="Тип счётчика", pattern="^(WATER|ELECTRICITY)$")
    serial_number: str | None = Field(None, description="Серийный номер", max_length=100)
    installation_date: datetime | None = Field(None, description="Дата установки")
    status: str = Field("active", description="Статус", pattern="^(active|inactive)$")


class MeterCreate(MeterBase):
    """Schema for creating a Meter."""

    pass


class MeterUpdate(BaseModel):
    """Schema for updating a Meter."""

    meter_type: str | None = Field(None, description="Тип счётчика", pattern="^(WATER|ELECTRICITY)$")
    serial_number: str | None = Field(None, description="Серийный номер", max_length=100)
    installation_date: datetime | None = Field(None, description="Дата установки")
    status: str | None = Field(None, description="Статус", pattern="^(active|inactive)$")


class MeterInDB(MeterBase):
    """Schema for Meter with DB fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class MeterReadingBase(BaseModel):
    """Base schema for MeterReading."""

    meter_id: UUID = Field(..., description="ID счётчика")
    reading_value: Decimal = Field(..., description="Значение показания", gt=0)
    reading_date: datetime = Field(..., description="Дата показания")


class MeterReadingCreate(MeterReadingBase):
    """Schema for creating a MeterReading."""

    pass


class MeterReadingInDB(MeterReadingBase):
    """Schema for MeterReading with DB fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
