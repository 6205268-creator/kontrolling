"""Meters domain entities."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.modules.shared.kernel.entities import BaseEntity


@dataclass
class Meter(BaseEntity):
    """Прибор учёта — счётчик воды или электроэнергии."""

    owner_id: UUID
    meter_type: str  # WATER, ELECTRICITY
    serial_number: str | None = None
    installation_date: datetime | None = None
    status: str = "active"  # active, inactive
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class MeterReading(BaseEntity):
    """Показание прибора учёта."""

    meter_id: UUID
    reading_value: Decimal
    reading_date: datetime
    created_at: datetime | None = None
