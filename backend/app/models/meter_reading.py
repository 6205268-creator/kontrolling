from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Guid


class MeterReading(Base):
    """Показание прибора учёта.

    Записывается по дате снятия показания. На одну дату возможен
    только один запись показания для каждого счётчика.
    """

    __tablename__ = "meter_readings"
    __table_args__ = (
        UniqueConstraint(
            "meter_id",
            "reading_date",
            name="uq_meter_readings_meter_date",
        ),
        {"comment": "Показания приборов учёта (вода, электроэнергия)"},
    )

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    meter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("meters.id"), nullable=False, index=True)
    reading_value: Mapped[Decimal] = mapped_column(nullable=False)
    reading_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    meter: Mapped["Meter"] = relationship("Meter", back_populates="readings")
