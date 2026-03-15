"""Cooperative SQLAlchemy model.

SQLAlchemy ORM model for database operations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Guid

if TYPE_CHECKING:
    from app.modules.administration.infrastructure.models import AppUserModel
    from app.modules.expenses.infrastructure.models import ExpenseModel
    from app.modules.financial_core.infrastructure.models import FinancialSubjectModel
    from app.modules.land_management.infrastructure.models import LandPlotModel


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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        comment="Дата и время последнего обновления записи",
    )

    # Relationships
    land_plots: Mapped[list["LandPlotModel"]] = relationship(
        "LandPlotModel", back_populates="cooperative"
    )
    financial_subjects: Mapped[list["FinancialSubjectModel"]] = relationship(
        "FinancialSubjectModel", back_populates="cooperative"
    )
    expenses: Mapped[list["ExpenseModel"]] = relationship(
        "ExpenseModel", back_populates="cooperative"
    )
    users: Mapped[list["AppUserModel"]] = relationship("AppUserModel", back_populates="cooperative")

    # Payment Distribution module relationships
    # NOTE: members, personal_accounts, settings_modules relationships are defined in payment_distribution module
    # via back_populates on MemberModel, PersonalAccountModel, SettingsModuleModel
    # personal_accounts: Mapped[list["PersonalAccountModel"]] = relationship("PersonalAccountModel", back_populates="cooperative")
    # settings_modules: Mapped[list["SettingsModuleModel"]] = relationship("SettingsModuleModel", back_populates="cooperative")
