import uuid
from datetime import UTC, date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Guid
from app.models.land_plot import LandPlot
from app.models.owner import Owner


class PlotOwnership(Base):
    """Право собственности на земельный участок.

    Связывает владельца (Owner) с участком (LandPlot) на определённый период.
    Поддерживает долевую собственность (например, 1/2, 1/3).
    is_primary=True означает, что владелец является членом СТ.
    """

    __tablename__ = "plot_ownerships"
    __table_args__ = (
        CheckConstraint("share_numerator <= share_denominator", name="ck_plot_ownership_share"),
        {"comment": "Права собственности на земельные участки (периоды и доли)"},
    )

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    land_plot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("land_plots.id"), nullable=False, index=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("owners.id"), nullable=False, index=True)
    share_numerator: Mapped[int] = mapped_column(Integer, nullable=False)
    share_denominator: Mapped[int] = mapped_column(Integer, nullable=False)
    is_primary: Mapped[bool] = mapped_column(nullable=False, default=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        comment="Дата и время последнего обновления записи",
    )

    land_plot: Mapped["LandPlot"] = relationship("LandPlot", back_populates="plot_ownerships")
    owner: Mapped["Owner"] = relationship("Owner", back_populates="plot_ownerships")
