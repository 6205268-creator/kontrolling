from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Guid


class Cooperative(Base):
    """Садоводческое товарищество (СТ).

    Основная организация-владелец земельных участков.
    Каждое СТ независимо и имеет своих владельцев, участки, финансы.
    """

    __tablename__ = "cooperatives"
    __table_args__ = (
        {"comment": "Садоводческие товарищества (СТ) — основные организации в системе", "extend_existing": True}
    )

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    unp: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        comment="Дата и время последнего обновления записи",
    )

    land_plots: Mapped[list["LandPlot"]] = relationship("LandPlot", back_populates="cooperative")
    financial_subjects: Mapped[list["FinancialSubject"]] = relationship(
        "FinancialSubject", back_populates="cooperative"
    )
    expenses: Mapped[list["Expense"]] = relationship("Expense", back_populates="cooperative")
    users: Mapped[list["AppUser"]] = relationship("AppUser", back_populates="cooperative")
