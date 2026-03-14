"""Accruals SQLAlchemy models.

SQLAlchemy ORM models for database operations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Guid


class AccrualModel(Base):
    """SQLAlchemy model for Accrual.

    Начисление по финансовому субъекту.
    """

    __tablename__ = "accruals"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_accruals_amount_non_negative"),
        {"comment": "Начисления по финансовым субъектам (взносы, услуги)", "extend_existing": True},
    )

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    financial_subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("financial_subjects.id"),
        nullable=False,
        index=True,
        comment="ID финансового субъекта",
    )
    contribution_type_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contribution_types.id"),
        nullable=False,
        index=True,
        comment="ID вида взноса (членский, целевой и т.д.)",
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    accrual_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="created")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        comment="Дата и время последнего обновления записи",
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Guid(), ForeignKey("app_users.id"), nullable=True
    )
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    operation_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Relationships - using string references to avoid circular imports
    # financial_subject: Mapped["FinancialSubjectModel"] = relationship("FinancialSubjectModel", back_populates="accruals")
    # contribution_type: Mapped["ContributionTypeModel"] = relationship("ContributionTypeModel", back_populates="accruals")

    def to_domain(self) -> "Accrual":
        """Convert SQLAlchemy model to domain entity."""
        from app.modules.accruals.domain.entities import Accrual

        return Accrual(
            id=self.id,
            financial_subject_id=self.financial_subject_id,
            contribution_type_id=self.contribution_type_id,
            amount=self.amount,
            accrual_date=self.accrual_date,
            period_start=self.period_start,
            period_end=self.period_end,
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at,
            cancelled_at=self.cancelled_at,
            cancelled_by_user_id=self.cancelled_by_user_id,
            cancellation_reason=self.cancellation_reason,
            operation_number=self.operation_number,
        )

    @classmethod
    def from_domain(cls, entity: "Accrual") -> "AccrualModel":
        """Create SQLAlchemy model from domain entity."""
        return cls(
            id=entity.id,
            financial_subject_id=entity.financial_subject_id,
            contribution_type_id=entity.contribution_type_id,
            amount=entity.amount,
            accrual_date=entity.accrual_date,
            period_start=entity.period_start,
            period_end=entity.period_end,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            cancelled_at=entity.cancelled_at,
            cancelled_by_user_id=entity.cancelled_by_user_id,
            cancellation_reason=entity.cancellation_reason,
            operation_number=entity.operation_number,
        )


class AccrualHistoryModel(Base):
    """SQLAlchemy model for Accrual history.

    История изменений начислений.
    """

    __tablename__ = "accruals_history"
    __table_args__ = {"comment": "Аудит изменений начислений", "extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False, index=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    operation: Mapped[str] = mapped_column(String(10), nullable=False)

    financial_subject_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False)
    contribution_type_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    accrual_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_by_user_id: Mapped[uuid.UUID | None] = mapped_column(Guid(), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    operation_number: Mapped[str | None] = mapped_column(String(50), nullable=True)


class ContributionTypeModel(Base):
    """SQLAlchemy model for ContributionType.

    Вид взноса — справочник типов начислений.
    """

    __tablename__ = "contribution_types"
    __table_args__ = {
        "comment": "Справочник видов взносов (членский, целевой, за услуги)",
        "extend_existing": True,
    }

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # accruals: Mapped[list["AccrualModel"]] = relationship("AccrualModel", back_populates="contribution_type")

    # Relationship for Payment Distribution module
    # NOTE: Disabled to avoid circular import issues during SQLAlchemy initialization
    # distribution_rules and settings relationships are defined in payment_distribution module
    # distribution_rules: Mapped[list["PaymentDistributionRuleModel"]] = relationship(...)
    # settings: Mapped[list["ContributionTypeSettingsModel"]] = relationship(...)

    def to_domain(self) -> "ContributionType":
        """Convert SQLAlchemy model to domain entity."""
        from app.modules.accruals.domain.entities import ContributionType

        return ContributionType(
            id=self.id,
            name=self.name,
            code=self.code,
            description=self.description,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: "ContributionType") -> "ContributionTypeModel":
        """Create SQLAlchemy model from domain entity."""
        kwargs: dict = {
            "name": entity.name,
            "code": entity.code,
            "description": entity.description,
            "created_at": entity.created_at,
        }
        if entity.id is not None:
            kwargs["id"] = entity.id
        return cls(**kwargs)
