"""Meters SQLAlchemy models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Guid


class MeterModel(Base):
    """SQLAlchemy model for Meter."""

    __tablename__ = "meters"
    __table_args__ = {"comment": "Приборы учёта (счётчики воды и электроэнергии)", "extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("owners.id"), nullable=False, index=True)
    meter_type: Mapped[str] = mapped_column(String(20), nullable=False)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    installation_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def to_domain(self) -> "Meter":
        """Convert to domain entity."""
        from app.modules.meters.domain.entities import Meter
        return Meter(
            id=self.id,
            owner_id=self.owner_id,
            meter_type=self.meter_type,
            serial_number=self.serial_number,
            installation_date=self.installation_date,
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, entity: "Meter") -> "MeterModel":
        """Create from domain entity."""
        return cls(
            id=entity.id,
            owner_id=entity.owner_id,
            meter_type=entity.meter_type,
            serial_number=entity.serial_number,
            installation_date=entity.installation_date,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class MeterReadingModel(Base):
    """SQLAlchemy model for MeterReading."""

    __tablename__ = "meter_readings"
    __table_args__ = (
        UniqueConstraint("meter_id", "reading_date", name="uq_meter_readings_meter_date"),
        {"comment": "Показания приборов учёта (вода, электроэнергия)", "extend_existing": True},
    )

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    meter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("meters.id"), nullable=False, index=True)
    reading_value: Mapped[Decimal] = mapped_column(nullable=False)
    reading_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    def to_domain(self) -> "MeterReading":
        """Convert to domain entity."""
        from app.modules.meters.domain.entities import MeterReading
        return MeterReading(
            id=self.id,
            meter_id=self.meter_id,
            reading_value=self.reading_value,
            reading_date=self.reading_date,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: "MeterReading") -> "MeterReadingModel":
        """Create from domain entity."""
        return cls(
            id=entity.id,
            meter_id=entity.meter_id,
            reading_value=entity.reading_value,
            reading_date=entity.reading_date,
            created_at=entity.created_at,
        )
