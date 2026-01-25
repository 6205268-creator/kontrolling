from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKeyConstraint, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PlotOwner(Base):
    __tablename__ = "plot_owner"
    __table_args__ = (
        UniqueConstraint(
            "snt_id",
            "plot_id",
            "owner_id",
            "date_from",
            name="uq_plot_owner_period",
        ),
        ForeignKeyConstraint(
            ["snt_id"],
            ["snt.id"],
            name="fk_plot_owner_snt",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["snt_id", "plot_id"],
            ["plot.snt_id", "plot.id"],
            name="fk_plot_owner_plot",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["snt_id", "owner_id"],
            ["owner.snt_id", "owner.id"],
            name="fk_plot_owner_owner",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snt_id: Mapped[int] = mapped_column(Integer, nullable=False)

    plot_id: Mapped[int] = mapped_column(Integer, nullable=False)
    owner_id: Mapped[int] = mapped_column(Integer, nullable=False)

    date_from: Mapped[date] = mapped_column(Date, nullable=False)
    date_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

