"""Payment Distribution SQLAlchemy models.

SQLAlchemy ORM models for database operations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Guid


class MemberModel(Base):
    """SQLAlchemy model for Member.

    Член СТ — техническая сущность связи Owner ↔ Cooperative.
    """

    __tablename__ = "members"
    __table_args__ = (
        UniqueConstraint("owner_id", "cooperative_id", name="uq_members_owner_cooperative"),
        {"comment": "Члены СТ (связь Owner ↔ Cooperative)", "extend_existing": True},
    )

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("owners.id"),
        nullable=False,
        index=True,
        comment="ID владельца",
    )
    cooperative_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cooperatives.id"),
        nullable=False,
        index=True,
        comment="ID СТ",
    )
    personal_account_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("personal_accounts.id"),
        nullable=True,
        comment="ID лицевого счёта",
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> "Member":
        """Convert SQLAlchemy model to domain entity."""
        from app.modules.payment_distribution.domain.entities import Member

        return Member(
            id=self.id,
            owner_id=self.owner_id,
            cooperative_id=self.cooperative_id,
            personal_account_id=self.personal_account_id,
            status=self.status,
            joined_at=self.joined_at,
            closed_at=self.closed_at,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: "Member") -> "MemberModel":
        """Create SQLAlchemy model from domain entity."""
        return cls(
            id=entity.id,
            owner_id=entity.owner_id,
            cooperative_id=entity.cooperative_id,
            personal_account_id=entity.personal_account_id,
            status=entity.status,
            joined_at=entity.joined_at,
            closed_at=entity.closed_at,
            created_at=entity.created_at,
        )


class PersonalAccountModel(Base):
    """SQLAlchemy model for PersonalAccount.

    Лицевой счёт члена СТ.
    """

    __tablename__ = "personal_accounts"
    __table_args__ = (
        UniqueConstraint("account_number", name="uq_personal_accounts_number"),
        CheckConstraint("balance >= 0", name="ck_personal_accounts_balance_non_negative"),
        {"comment": "Лицевые счета членов СТ", "extend_existing": True},
    )

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id"),
        nullable=False,
        index=True,
        comment="ID члена СТ",
    )
    cooperative_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cooperatives.id"),
        nullable=False,
        index=True,
        comment="ID СТ",
    )
    account_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> "PersonalAccount":
        """Convert SQLAlchemy model to domain entity."""
        from app.modules.payment_distribution.domain.entities import PersonalAccount
        from app.modules.shared.kernel.money import Money

        return PersonalAccount(
            id=self.id,
            member_id=self.member_id,
            cooperative_id=self.cooperative_id,
            account_number=self.account_number,
            balance=Money(self.balance),
            status=self.status,
            opened_at=self.opened_at,
            closed_at=self.closed_at,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: "PersonalAccount") -> "PersonalAccountModel":
        """Create SQLAlchemy model from domain entity."""
        return cls(
            id=entity.id,
            member_id=entity.member_id,
            cooperative_id=entity.cooperative_id,
            account_number=entity.account_number,
            balance=entity.balance.amount,
            status=entity.status,
            opened_at=entity.opened_at,
            closed_at=entity.closed_at,
            created_at=entity.created_at,
        )


class PersonalAccountTransactionModel(Base):
    """SQLAlchemy model for PersonalAccountTransaction.

    Транзакция по лицевому счёту.
    """

    __tablename__ = "personal_account_transactions"
    __table_args__ = (
        CheckConstraint(
            "amount >= 0", name="ck_pa_transactions_amount_non_negative"
        ),
        {"comment": "Транзакции по лицевым счетам", "extend_existing": True},
    )

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("personal_accounts.id"),
        nullable=False,
        index=True,
        comment="ID лицевого счёта",
    )
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("payments.id"),
        nullable=True,
        index=True,
        comment="ID платежа (если зачисление)",
    )
    distribution_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("payment_distributions.id"),
        nullable=True,
        index=True,
        comment="ID распределения (если списание)",
    )
    transaction_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # credit, debit
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> "PersonalAccountTransaction":
        """Convert SQLAlchemy model to domain entity."""
        from app.modules.payment_distribution.domain.entities import PersonalAccountTransaction
        from app.modules.shared.kernel.money import Money

        return PersonalAccountTransaction(
            id=self.id,
            account_id=self.account_id,
            payment_id=self.payment_id,
            distribution_id=self.distribution_id,
            transaction_number=self.transaction_number,
            transaction_date=self.transaction_date,
            amount=Money(self.amount),
            type=self.type,
            description=self.description,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: "PersonalAccountTransaction") -> "PersonalAccountTransactionModel":
        """Create SQLAlchemy model from domain entity."""
        return cls(
            id=entity.id,
            account_id=entity.account_id,
            payment_id=entity.payment_id,
            distribution_id=entity.distribution_id,
            transaction_number=entity.transaction_number,
            transaction_date=entity.transaction_date,
            amount=entity.amount.amount,
            type=entity.type,
            description=entity.description,
            created_at=entity.created_at,
        )


class PaymentDistributionModel(Base):
    """SQLAlchemy model for PaymentDistribution.

    Распределение платежа по начислению.
    """

    __tablename__ = "payment_distributions"
    __table_args__ = (
        CheckConstraint(
            "amount >= 0", name="ck_payment_distributions_amount_non_negative"
        ),
        {"comment": "Распределения платежей по начислениям", "extend_existing": True},
    )

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    payment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payments.id"),
        nullable=False,
        index=True,
        comment="ID платежа",
    )
    financial_subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("financial_subjects.id"),
        nullable=False,
        index=True,
        comment="ID финансового субъекта",
    )
    accrual_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("accruals.id"),
        nullable=True,
        index=True,
        comment="ID начисления (если известно)",
    )
    distribution_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    distributed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    priority: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="applied")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> "PaymentDistribution":
        """Convert SQLAlchemy model to domain entity."""
        from app.modules.payment_distribution.domain.entities import PaymentDistribution
        from app.modules.shared.kernel.money import Money

        return PaymentDistribution(
            id=self.id,
            payment_id=self.payment_id,
            financial_subject_id=self.financial_subject_id,
            accrual_id=self.accrual_id,
            distribution_number=self.distribution_number,
            distributed_at=self.distributed_at,
            amount=Money(self.amount),
            priority=self.priority,
            status=self.status,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: "PaymentDistribution") -> "PaymentDistributionModel":
        """Create SQLAlchemy model from domain entity."""
        return cls(
            id=entity.id,
            payment_id=entity.payment_id,
            financial_subject_id=entity.financial_subject_id,
            accrual_id=entity.accrual_id,
            distribution_number=entity.distribution_number,
            distributed_at=entity.distributed_at,
            amount=entity.amount.amount,
            priority=entity.priority,
            status=entity.status,
            created_at=entity.created_at,
        )
