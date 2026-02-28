from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Guid
from app.models.cooperative import Cooperative


class LandPlot(Base):
    """Земельный участок в садоводческом товариществе.

    Каждый участок принадлежит одному СТ и может иметь нескольких владельцев
    (через таблицу PlotOwnership). На участке могут располагаться приборы учёта.
    """

    __tablename__ = "land_plots"
    __table_args__ = (
        UniqueConstraint(
            "cooperative_id", "plot_number", name="uq_land_plots_cooperative_plot_number"
        ),
        {"comment": "Земельные участки в садоводческих товариществах"},
    )

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    cooperative_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cooperatives.id"), nullable=False, index=True
    )
    plot_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    area_sqm: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cadastral_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
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

    cooperative: Mapped["Cooperative"] = relationship("Cooperative", back_populates="land_plots")
    plot_ownerships: Mapped[list["PlotOwnership"]] = relationship(
        "PlotOwnership", back_populates="land_plot"
    )
