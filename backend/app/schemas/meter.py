from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MeterBase(BaseModel):
    """Базовая схема Meter."""

    owner_id: UUID = Field(..., description="ID владельца")
    meter_type: str = Field(..., description="Тип счётчика", pattern="^(WATER|ELECTRICITY)$")
    serial_number: str | None = Field(None, description="Серийный номер", max_length=100)
    installation_date: datetime | None = Field(None, description="Дата установки")
    status: str = Field("active", description="Статус", pattern="^(active|inactive)$")


class MeterCreate(MeterBase):
    """Схема для создания Meter."""

    pass


class MeterUpdate(BaseModel):
    """Схема для обновления Meter."""

    meter_type: str | None = Field(None, description="Тип счётчика", pattern="^(WATER|ELECTRICITY)$")
    serial_number: str | None = Field(None, description="Серийный номер", max_length=100)
    installation_date: datetime | None = Field(None, description="Дата установки")
    status: str | None = Field(None, description="Статус", pattern="^(active|inactive)$")


class MeterInDB(MeterBase):
    """Схема Meter с полями БД."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class MeterReadingBase(BaseModel):
    """Базовая схема MeterReading."""

    meter_id: UUID = Field(..., description="ID счётчика")
    reading_value: Decimal = Field(..., description="Показание", ge=0)
    reading_date: datetime = Field(..., description="Дата снятия показания")


class MeterReadingCreate(MeterReadingBase):
    """Схема для создания MeterReading."""

    pass


class MeterReadingInDB(MeterReadingBase):
    """Схема MeterReading с полями БД."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
