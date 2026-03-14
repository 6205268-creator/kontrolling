"""
SQLAlchemy ORM models for Payment Distribution module.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Guid


class MemberModel(Base):
    """Член СТ (ORM модель)."""

    __tablename__ = "members"

    id: Mapped[UUID] = mapped_column(Guid, primary_key=True, index=True)
    owner_id: Mapped[UUID] = mapped_column(
        Guid, ForeignKey("owners.id"), nullable=False, index=True
    )
    cooperative_id: Mapped[UUID] = mapped_column(
        Guid, ForeignKey("cooperatives.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    joined_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    owner = relationship("OwnerModel", back_populates="members")
    cooperative = relationship("CooperativeModel", back_populates="members")
    plots = relationship("MemberPlotModel", back_populates="member", cascade="all, delete-orphan")
    personal_account = relationship(
        "PersonalAccountModel",
        back_populates="member",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("owner_id", "cooperative_id", name="uq_members_owner_cooperative"),
        Index("ix_members_status", "status"),
    )


class MemberPlotModel(Base):
    """Участки члена СТ (ORM модель)."""

    __tablename__ = "member_plots"

    id: Mapped[UUID] = mapped_column(Guid, primary_key=True, index=True)
    member_id: Mapped[UUID] = mapped_column(
        Guid, ForeignKey("members.id"), nullable=False, index=True
    )
    land_plot_id: Mapped[UUID] = mapped_column(
        Guid, ForeignKey("land_plots.id"), nullable=False, index=True
    )
    share_numerator: Mapped[int] = mapped_column(Integer, nullable=False)
    share_denominator: Mapped[int] = mapped_column(Integer, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    member = relationship("MemberModel", back_populates="plots")
    land_plot = relationship("LandPlotModel", back_populates="member_plots")

    __table_args__ = (
        Index("ix_member_plots_member", "member_id"),
        Index("ix_member_plots_land_plot", "land_plot_id"),
    )


class PersonalAccountModel(Base):
    """Лицевой счёт (ORM модель)."""

    __tablename__ = "personal_accounts"

    id: Mapped[UUID] = mapped_column(Guid, primary_key=True, index=True)
    member_id: Mapped[UUID] = mapped_column(
        Guid, ForeignKey("members.id"), nullable=False, index=True
    )
    cooperative_id: Mapped[UUID] = mapped_column(
        Guid, ForeignKey("cooperatives.id"), nullable=False, index=True
    )
    account_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    balance: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    opened_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    member = relationship("MemberModel", back_populates="personal_account")
    cooperative = relationship("CooperativeModel", back_populates="personal_accounts")
    transactions = relationship(
        "PersonalAccountTransactionModel",
        back_populates="account",
        cascade="all, delete-orphan",
        order_by="PersonalAccountTransactionModel.transaction_date.desc()",
    )

    __table_args__ = (
        Index("ix_accounts_cooperative_status", "cooperative_id", "status"),
        Index("ix_accounts_member", "member_id"),
    )


class PersonalAccountTransactionModel(Base):
    """Операция по лицевому счёту (ORM модель)."""

    __tablename__ = "personal_account_transactions"

    id: Mapped[UUID] = mapped_column(Guid, primary_key=True, index=True)
    account_id: Mapped[UUID] = mapped_column(
        Guid, ForeignKey("personal_accounts.id"), nullable=False, index=True
    )
    payment_id: Mapped[UUID | None] = mapped_column(
        Guid, ForeignKey("payments.id"), nullable=True, index=True
    )
    distribution_id: Mapped[UUID | None] = mapped_column(
        Guid, ForeignKey("payment_distributions.id"), nullable=True, index=True
    )
    transaction_number: Mapped[str] = mapped_column(String(50), nullable=False)
    transaction_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    account = relationship("PersonalAccountModel", back_populates="transactions")
    payment = relationship("PaymentModel", back_populates="transactions")
    distribution = relationship("PaymentDistributionModel", back_populates="transaction")

    __table_args__ = (
        Index("ix_transactions_account_date", "account_id", "transaction_date"),
        Index("ix_transactions_type", "type"),
    )


class PaymentDistributionModel(Base):
    """Распределение платежа (ORM модель)."""

    __tablename__ = "payment_distributions"

    id: Mapped[UUID] = mapped_column(Guid, primary_key=True, index=True)
    payment_id: Mapped[UUID] = mapped_column(
        Guid, ForeignKey("payments.id"), nullable=False, index=True
    )
    financial_subject_id: Mapped[UUID] = mapped_column(
        Guid, ForeignKey("financial_subjects.id"), nullable=False, index=True
    )
    distribution_number: Mapped[str] = mapped_column(String(50), nullable=False)
    distributed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="applied")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    payment = relationship("PaymentModel", back_populates="distributions")
    financial_subject = relationship("FinancialSubjectModel", back_populates="distributions")
    transaction = relationship(
        "PersonalAccountTransactionModel",
        back_populates="distribution",
        uselist=False,
    )

    __table_args__ = (
        Index("ix_distributions_payment", "payment_id"),
        Index("ix_distributions_financial_subject", "financial_subject_id"),
        Index("ix_distributions_status", "status"),
    )


class SettingsModuleModel(Base):
    """Модуль настроек (ORM модель)."""

    __tablename__ = "settings_modules"

    id: Mapped[UUID] = mapped_column(Guid, primary_key=True, index=True)
    cooperative_id: Mapped[UUID] = mapped_column(
        Guid, ForeignKey("cooperatives.id"), nullable=False, index=True
    )
    module_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    cooperative = relationship("CooperativeModel", back_populates="settings_modules")
    distribution_rules = relationship(
        "PaymentDistributionRuleModel",
        back_populates="settings_module",
        cascade="all, delete-orphan",
    )
    contribution_settings = relationship(
        "ContributionTypeSettingsModel",
        back_populates="settings_module",
        cascade="all, delete-orphan",
    )
    meter_tariffs = relationship(
        "MeterTariffModel",
        back_populates="settings_module",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("cooperative_id", "module_name", name="uq_settings_module_coop_name"),
        Index("ix_settings_modules_cooperative", "cooperative_id"),
    )


class PaymentDistributionRuleModel(Base):
    """Правило распределения платежей (ORM модель)."""

    __tablename__ = "payment_distribution_rules"

    id: Mapped[UUID] = mapped_column(Guid, primary_key=True, index=True)
    settings_module_id: Mapped[UUID] = mapped_column(
        Guid, ForeignKey("settings_modules.id"), nullable=False, index=True
    )
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    contribution_type_id: Mapped[UUID | None] = mapped_column(
        Guid, ForeignKey("contribution_types.id"), nullable=True, index=True
    )
    meter_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    settings_module = relationship("SettingsModuleModel", back_populates="distribution_rules")
    contribution_type = relationship("ContributionTypeModel", back_populates="distribution_rules")

    __table_args__ = (
        UniqueConstraint(
            "settings_module_id", "priority", name="uq_distribution_rule_module_priority"
        ),
        Index("ix_distribution_rules_module", "settings_module_id"),
        Index("ix_distribution_rules_type", "rule_type"),
    )


class ContributionTypeSettingsModel(Base):
    """Настройки вида взноса (ORM модель)."""

    __tablename__ = "contribution_type_settings"

    id: Mapped[UUID] = mapped_column(Guid, primary_key=True, index=True)
    settings_module_id: Mapped[UUID] = mapped_column(
        Guid, ForeignKey("settings_modules.id"), nullable=False, index=True
    )
    contribution_type_id: Mapped[UUID] = mapped_column(
        Guid, ForeignKey("contribution_types.id"), nullable=False, index=True
    )
    default_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    calculation_period: Mapped[str] = mapped_column(String(50), nullable=False, default="year")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    settings_module = relationship("SettingsModuleModel", back_populates="contribution_settings")
    contribution_type = relationship("ContributionTypeModel", back_populates="settings")

    __table_args__ = (
        UniqueConstraint(
            "settings_module_id",
            "contribution_type_id",
            name="uq_contribution_type_settings_module_type",
        ),
    )


class MeterTariffModel(Base):
    """Тариф на ресурсы (ORM модель)."""

    __tablename__ = "meter_tariffs"

    id: Mapped[UUID] = mapped_column(Guid, primary_key=True, index=True)
    settings_module_id: Mapped[UUID] = mapped_column(
        Guid, ForeignKey("settings_modules.id"), nullable=False, index=True
    )
    meter_type: Mapped[str] = mapped_column(String(50), nullable=False)
    tariff_per_unit: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    settings_module = relationship("SettingsModuleModel", back_populates="meter_tariffs")

    __table_args__ = (
        Index("ix_meter_tariffs_module", "settings_module_id"),
        Index("ix_meter_tariffs_type", "meter_type"),
        Index("ix_meter_tariffs_valid_from", "valid_from"),
    )
