"""Financial Core SQLAlchemy models.

SQLAlchemy ORM models for database operations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Guid
from app.modules.financial_core.domain.entities import SubjectType


def generate_financial_subject_code() -> str:
    """Generate unique code for payment documents: FS-{short_uuid}."""
    return f"FS-{uuid.uuid4().hex[:8].upper()}"


class FinancialSubjectModel(Base):
    """SQLAlchemy model for FinancialSubject.

    Финансовый субъект — центр финансовой ответственности.
    """

    __tablename__ = "financial_subjects"
    __table_args__ = (
        UniqueConstraint(
            "subject_type",
            "subject_id",
            "cooperative_id",
            name="uq_financial_subjects_type_subject_coop",
        ),
        {
            "comment": "Финансовые субъекты — центры финансовой ответственности (участки, счётчики, решения)",
            "extend_existing": True,
        },
    )

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    subject_type: Mapped[str] = mapped_column(String(30), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False)
    cooperative_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cooperatives.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, default=generate_financial_subject_code
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships - using string references to avoid circular imports
    # cooperative: Mapped["CooperativeModel"] = relationship("CooperativeModel", back_populates="financial_subjects")
    # accruals: Mapped[list["AccrualModel"]] = relationship("AccrualModel", back_populates="financial_subject")
    # payments: Mapped[list["PaymentModel"]] = relationship("PaymentModel", back_populates="financial_subject")

    def to_domain(self) -> "FinancialSubject":
        """Convert SQLAlchemy model to domain entity."""
        from app.modules.financial_core.domain.entities import FinancialSubject

        return FinancialSubject(
            id=self.id,
            subject_type=SubjectType(self.subject_type),
            subject_id=self.subject_id,
            cooperative_id=self.cooperative_id,
            code=self.code,
            status=self.status,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: "FinancialSubject") -> "FinancialSubjectModel":
        """Create SQLAlchemy model from domain entity."""
        return cls(
            id=entity.id,
            subject_type=entity.subject_type,
            subject_id=entity.subject_id,
            cooperative_id=entity.cooperative_id,
            code=entity.code,
            status=entity.status,
            created_at=entity.created_at,
        )


class FinancialPeriodModel(Base):
    """SQLAlchemy model for FinancialPeriod.

    Финансовый период — отчётный период для закрытия данных.
    """

    __tablename__ = "financial_periods"
    __table_args__ = (
        UniqueConstraint(
            "cooperative_id",
            "year",
            "month",
            name="uq_financial_periods_coop_year_month",
        ),
        Index(
            "uq_financial_periods_yearly_unique",
            "cooperative_id",
            "year",
            unique=True,
            postgresql_where=text("period_type = 'yearly'"),
            sqlite_where=text("period_type = 'yearly'"),
        ),
        {
            "comment": "Финансовые периоды (месячные и годовые) для закрытия данных",
            "extend_existing": True,
        },
    )

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    cooperative_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cooperatives.id"), nullable=False, index=True
    )
    period_type: Mapped[str] = mapped_column(String(20), nullable=False)  # monthly, yearly
    year: Mapped[int] = mapped_column(nullable=False)
    month: Mapped[int | None] = mapped_column(nullable=True)  # 1-12 for monthly, NULL for yearly
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> "FinancialPeriod":
        """Convert SQLAlchemy model to domain entity."""
        from app.modules.financial_core.domain.entities import FinancialPeriod, PeriodType

        return FinancialPeriod(
            id=self.id,
            cooperative_id=self.cooperative_id,
            period_type=PeriodType(self.period_type),
            year=self.year,
            month=self.month,
            start_date=self.start_date,
            end_date=self.end_date,
            status=self.status,
            closed_at=self.closed_at,
            closed_by_user_id=self.closed_by_user_id,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: "FinancialPeriod") -> "FinancialPeriodModel":
        """Create SQLAlchemy model from domain entity."""
        return cls(
            id=entity.id,
            cooperative_id=entity.cooperative_id,
            period_type=entity.period_type.value,
            year=entity.year,
            month=entity.month,
            start_date=entity.start_date,
            end_date=entity.end_date,
            status=entity.status,
            closed_at=entity.closed_at,
            closed_by_user_id=entity.closed_by_user_id,
            created_at=entity.created_at,
        )


class BalanceSnapshotModel(Base):
    """SQLAlchemy model for BalanceSnapshot.

    Снимок баланса финансового субъекта на конец периода.
    """

    __tablename__ = "balance_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "financial_subject_id",
            "period_id",
            name="uq_balance_snapshots_subject_period",
        ),
        {
            "comment": "Снимки балансов финансовых субъектов на конец периода",
            "extend_existing": True,
        },
    )

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    financial_subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("financial_subjects.id"), nullable=False, index=True
    )
    period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("financial_periods.id"), nullable=False, index=True
    )
    cooperative_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cooperatives.id"), nullable=False, index=True
    )
    total_accruals: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_payments: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> "BalanceSnapshot":
        """Convert SQLAlchemy model to domain entity."""
        from app.modules.financial_core.domain.entities import BalanceSnapshot
        from app.modules.shared.kernel.money import Money

        return BalanceSnapshot(
            id=self.id,
            financial_subject_id=self.financial_subject_id,
            period_id=self.period_id,
            cooperative_id=self.cooperative_id,
            total_accruals=Money(self.total_accruals),
            total_payments=Money(self.total_payments),
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: "BalanceSnapshot") -> "BalanceSnapshotModel":
        """Create SQLAlchemy model from domain entity."""
        return cls(
            id=entity.id,
            financial_subject_id=entity.financial_subject_id,
            period_id=entity.period_id,
            cooperative_id=entity.cooperative_id,
            total_accruals=entity.total_accruals.amount,
            total_payments=entity.total_payments.amount,
            balance=entity.balance.amount,
            created_at=entity.created_at,
        )


class DebtLineModel(Base):
    """Строка долга по начислению (фаза 5)."""

    __tablename__ = "debt_lines"
    __table_args__ = (
        Index("ix_debt_lines_coop_status", "cooperative_id", "status"),
        {"comment": "Строки долга по начислениям", "extend_existing": True},
    )

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    cooperative_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cooperatives.id"), nullable=False, index=True
    )
    financial_subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("financial_subjects.id"), nullable=False, index=True
    )
    accrual_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("accruals.id"), nullable=False, unique=True
    )
    contribution_type_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contribution_types.id"), nullable=False
    )
    original_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    overdue_since: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> "DebtLine":
        from app.modules.financial_core.domain.entities import DebtLine
        from app.modules.shared.kernel.money import Money

        return DebtLine(
            id=self.id,
            cooperative_id=self.cooperative_id,
            financial_subject_id=self.financial_subject_id,
            accrual_id=self.accrual_id,
            contribution_type_id=self.contribution_type_id,
            original_amount=Money(self.original_amount),
            paid_amount=Money(self.paid_amount),
            due_date=self.due_date,
            overdue_since=self.overdue_since,
            status=self.status,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: "DebtLine") -> "DebtLineModel":
        return cls(
            id=entity.id,
            cooperative_id=entity.cooperative_id,
            financial_subject_id=entity.financial_subject_id,
            accrual_id=entity.accrual_id,
            contribution_type_id=entity.contribution_type_id,
            original_amount=entity.original_amount.amount,
            paid_amount=entity.paid_amount.amount,
            due_date=entity.due_date,
            overdue_since=entity.overdue_since,
            status=entity.status,
            created_at=entity.created_at,
        )


class PenaltySettingsModel(Base):
    """Настройки расчёта пеней."""

    __tablename__ = "penalty_settings"
    __table_args__ = (
        Index("ix_penalty_settings_coop_type", "cooperative_id", "contribution_type_id"),
        {"comment": "Настройки пеней по СТ", "extend_existing": True},
    )

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    cooperative_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cooperatives.id"), nullable=False, index=True
    )
    contribution_type_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("contribution_types.id"), nullable=True
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    daily_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    grace_period_days: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> "PenaltySettings":
        from app.modules.financial_core.domain.entities import PenaltySettings

        return PenaltySettings(
            id=self.id,
            cooperative_id=self.cooperative_id,
            contribution_type_id=self.contribution_type_id,
            is_enabled=self.is_enabled,
            daily_rate=self.daily_rate,
            grace_period_days=self.grace_period_days,
            effective_from=self.effective_from,
            effective_to=self.effective_to,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: "PenaltySettings") -> "PenaltySettingsModel":
        return cls(
            id=entity.id,
            cooperative_id=entity.cooperative_id,
            contribution_type_id=entity.contribution_type_id,
            is_enabled=entity.is_enabled,
            daily_rate=entity.daily_rate,
            grace_period_days=entity.grace_period_days,
            effective_from=entity.effective_from,
            effective_to=entity.effective_to,
            created_at=entity.created_at,
        )
