"""Land Management SQLAlchemy models.

SQLAlchemy ORM models for database operations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Guid


class LandPlotModel(Base):
    """SQLAlchemy model for LandPlot.

    Земельный участок в садоводческом товариществе.
    """

    __tablename__ = "land_plots"
    __table_args__ = (
        UniqueConstraint(
            "cooperative_id", "plot_number", name="uq_land_plots_cooperative_plot_number"
        ),
        {"comment": "Земельные участки в садоводческих товариществах", "extend_existing": True},
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

    # Relationships - using string references to avoid circular imports
    # cooperative: Mapped["CooperativeModel"] = relationship("CooperativeModel", back_populates="land_plots")
    plot_ownerships: Mapped[list["PlotOwnershipModel"]] = relationship(
        "PlotOwnershipModel",
        back_populates="land_plot",
        foreign_keys="PlotOwnershipModel.land_plot_id",
    )

    def to_domain(self) -> "LandPlot":
        """Convert SQLAlchemy model to domain entity."""
        from app.modules.land_management.domain.entities import LandPlot

        return LandPlot(
            id=self.id,
            cooperative_id=self.cooperative_id,
            plot_number=self.plot_number,
            area_sqm=self.area_sqm,
            cadastral_number=self.cadastral_number,
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, entity: "LandPlot") -> "LandPlotModel":
        """Create SQLAlchemy model from domain entity."""
        return cls(
            id=entity.id,
            cooperative_id=entity.cooperative_id,
            plot_number=entity.plot_number,
            area_sqm=entity.area_sqm,
            cadastral_number=entity.cadastral_number,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class OwnerModel(Base):
    """SQLAlchemy model for Owner.

    Владелец (физическое или юридическое лицо).
    """

    __tablename__ = "owners"
    __table_args__ = {
        "comment": "Владельцы — физические и юридические лица, владеющие участками и приборами учёта",
        "extend_existing": True,
    }

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    owner_type: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tax_id: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        comment="Дата и время последнего обновления записи",
    )

    plot_ownerships: Mapped[list["PlotOwnershipModel"]] = relationship(
        "PlotOwnershipModel", back_populates="owner", foreign_keys="PlotOwnershipModel.owner_id"
    )
    # payments: Mapped[list["PaymentModel"]] = relationship("PaymentModel", back_populates="payer")
    # meters: Mapped[list["MeterModel"]] = relationship("MeterModel", back_populates="owner")

    def to_domain(self) -> "Owner":
        """Convert SQLAlchemy model to domain entity."""
        from app.modules.land_management.domain.entities import Owner

        return Owner(
            id=self.id,
            owner_type=self.owner_type,
            name=self.name,
            tax_id=self.tax_id,
            contact_phone=self.contact_phone,
            contact_email=self.contact_email,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, entity: "Owner") -> "OwnerModel":
        """Create SQLAlchemy model from domain entity."""
        return cls(
            id=entity.id,
            owner_type=entity.owner_type,
            name=entity.name,
            tax_id=entity.tax_id,
            contact_phone=entity.contact_phone,
            contact_email=entity.contact_email,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class PlotOwnershipModel(Base):
    """SQLAlchemy model for PlotOwnership.

    Право собственности на земельный участок.
    """

    __tablename__ = "plot_ownerships"
    __table_args__ = (
        CheckConstraint("share_numerator <= share_denominator", name="ck_plot_ownership_share"),
        {
            "comment": "Права собственности на земельные участки (периоды и доли)",
            "extend_existing": True,
        },
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

    land_plot: Mapped["LandPlotModel"] = relationship(
        "LandPlotModel", back_populates="plot_ownerships"
    )
    owner: Mapped["OwnerModel"] = relationship("OwnerModel", back_populates="plot_ownerships")

    def to_domain(self) -> "PlotOwnership":
        """Convert SQLAlchemy model to domain entity."""
        from app.modules.land_management.domain.entities import PlotOwnership

        return PlotOwnership(
            id=self.id,
            land_plot_id=self.land_plot_id,
            owner_id=self.owner_id,
            share_numerator=self.share_numerator,
            share_denominator=self.share_denominator,
            is_primary=self.is_primary,
            valid_from=self.valid_from,
            valid_to=self.valid_to,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, entity: "PlotOwnership") -> "PlotOwnershipModel":
        """Create SQLAlchemy model from domain entity."""
        return cls(
            id=entity.id,
            land_plot_id=entity.land_plot_id,
            owner_id=entity.owner_id,
            share_numerator=entity.share_numerator,
            share_denominator=entity.share_denominator,
            is_primary=entity.is_primary,
            valid_from=entity.valid_from,
            valid_to=entity.valid_to,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class PlotOwnershipHistoryModel(Base):
    """SQLAlchemy model for PlotOwnership history.

    История изменений прав собственности.
    """

    __tablename__ = "plot_ownerships_history"
    __table_args__ = {
        "comment": "Аудит изменений прав собственности на участки",
        "extend_existing": True,
    }

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False, index=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    operation: Mapped[str] = mapped_column(String(10), nullable=False)

    land_plot_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False)
    share_numerator: Mapped[int] = mapped_column(Integer, nullable=False)
    share_denominator: Mapped[int] = mapped_column(Integer, nullable=False)
    is_primary: Mapped[bool] = mapped_column(nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
