from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Guid


class Owner(Base):
    """Владелец (физическое или юридическое лицо).

    Может владеть земельными участками (через PlotOwnership),
    приборами учёта (Meter), а также совершать платежи.
    """

    __tablename__ = "owners"
    __table_args__ = {"comment": "Владельцы — физические и юридические лица, владеющие участками и приборами учёта"}

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    owner_type: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tax_id: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        comment="Дата и время последнего обновления записи",
    )

    plot_ownerships: Mapped[list["PlotOwnership"]] = relationship("PlotOwnership", back_populates="owner")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="payer")
    meters: Mapped[list["Meter"]] = relationship("Meter", back_populates="owner")
