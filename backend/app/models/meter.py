from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Guid


class Meter(Base):
    """Прибор учёта — счётчик воды или электроэнергии.

    Принадлежит владельцу (Owner). Показания счётчика записываются
    в MeterReading. Для начислений создаётся FinancialSubject
    с типом WATER_METER или ELECTRICITY_METER.
    Статусы: active (активен/установлен), inactive (не активен/снян).
    """

    __tablename__ = "meters"
    __table_args__ = {"comment": "Приборы учёта (счётчики воды и электроэнергии)"}

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("owners.id"), nullable=False, index=True)
    meter_type: Mapped[str] = mapped_column(String(20), nullable=False)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    installation_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        comment="Дата и время последнего обновления записи",
    )

    owner: Mapped["Owner"] = relationship("Owner", back_populates="meters")
    readings: Mapped[list["MeterReading"]] = relationship(
        "MeterReading", back_populates="meter", cascade="all, delete-orphan"
    )
