from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Meter(Base):
    __tablename__ = "meter"
    __table_args__ = (
        UniqueConstraint("snt_id", "plot_id", "meter_type", name="uq_meter_snt_plot_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snt_id: Mapped[int] = mapped_column(ForeignKey("snt.id", ondelete="RESTRICT"), nullable=False)
    plot_id: Mapped[int] = mapped_column(ForeignKey("plot.id", ondelete="RESTRICT"), nullable=False)
    meter_type: Mapped[str] = mapped_column(String(50), nullable=False)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
