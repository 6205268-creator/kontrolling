"""Cooperative SQLAlchemy model.

SQLAlchemy ORM model for database operations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Guid


class CooperativeModel(Base):
    """Садоводческое товарищество (СТ).

    Основная организация-владелец земельных участков.
    Каждое СТ независимо и имеет своих владельцев, участки, финансы.
    """

    __tablename__ = "cooperatives"
    __table_args__ = {
        "comment": "Садоводческие товарищества (СТ) — основные организации в системе",
        "extend_existing": True,
    }

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    unp: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    period_reopen_allowed_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
        comment="Сколько дней казначей может переоткрыть закрытый период",
    )
    penalty_accrual_schedule: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="monthly",
        comment="Автоначисление пеней: monthly, weekly, disabled",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        comment="Дата и время последнего обновления записи",
    )

    # Relationships - using string references to avoid circular imports
    # land_plots: Mapped[list["LandPlotModel"]] = relationship("LandPlotModel", back_populates="cooperative")
    # financial_subjects: Mapped[list["FinancialSubjectModel"]] = relationship("FinancialSubjectModel", back_populates="cooperative")
    # expenses: Mapped[list["ExpenseModel"]] = relationship("ExpenseModel", back_populates="cooperative")
    # users: Mapped[list["AppUserModel"]] = relationship("AppUserModel", back_populates="cooperative")
