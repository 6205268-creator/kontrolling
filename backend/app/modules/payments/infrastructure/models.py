"""Payments SQLAlchemy models."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Guid

if TYPE_CHECKING:
    from app.modules.financial_core.infrastructure.models import FinancialSubjectModel


class PaymentModel(Base):
    """SQLAlchemy model for Payment."""

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        {
            "comment": "Платежи по финансовым субъектам (поступления от владельцев)",
            "extend_existing": True,
        },
    )

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    financial_subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("financial_subjects.id"),
        nullable=False,
        index=True,
        comment="ID финансового субъекта",
    )
    payer_owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("owners.id"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    document_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="confirmed")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Guid(), ForeignKey("app_users.id"), nullable=True
    )
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    operation_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Relationships
    financial_subject: Mapped["FinancialSubjectModel"] = relationship("FinancialSubjectModel")
    # NOTE: distributions and transactions relationships are defined in payment_distribution module
    # via back_populates on PaymentDistributionModel and PersonalAccountTransactionModel
    # distributions: Mapped[list["PaymentDistributionModel"]] = relationship("PaymentDistributionModel", back_populates="payment")
    # transactions: Mapped[list["PersonalAccountTransactionModel"]] = relationship("PersonalAccountTransactionModel", back_populates="payment")

    def to_domain(self) -> "Payment":
        """Convert to domain entity."""
        from app.modules.payments.domain.entities import Payment

        return Payment(
            id=self.id,
            financial_subject_id=self.financial_subject_id,
            payer_owner_id=self.payer_owner_id,
            amount=self.amount,
            payment_date=self.payment_date,
            document_number=self.document_number,
            description=self.description,
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at,
            cancelled_at=self.cancelled_at,
            cancelled_by_user_id=self.cancelled_by_user_id,
            cancellation_reason=self.cancellation_reason,
            operation_number=self.operation_number,
        )

    @classmethod
    def from_domain(cls, entity: "Payment") -> "PaymentModel":
        """Create from domain entity."""
        return cls(
            id=entity.id,
            financial_subject_id=entity.financial_subject_id,
            payer_owner_id=entity.payer_owner_id,
            amount=entity.amount,
            payment_date=entity.payment_date,
            document_number=entity.document_number,
            description=entity.description,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            cancelled_at=entity.cancelled_at,
            cancelled_by_user_id=entity.cancelled_by_user_id,
            cancellation_reason=entity.cancellation_reason,
            operation_number=entity.operation_number,
        )


class PaymentHistoryModel(Base):
    """SQLAlchemy model for Payment history."""

    __tablename__ = "payments_history"
    __table_args__ = {"comment": "Аудит изменений платежей", "extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False, index=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    operation: Mapped[str] = mapped_column(String(10), nullable=False)

    financial_subject_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False)
    payer_owner_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    document_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_by_user_id: Mapped[uuid.UUID | None] = mapped_column(Guid(), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    operation_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
