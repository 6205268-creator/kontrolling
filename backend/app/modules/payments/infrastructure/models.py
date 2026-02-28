"""Payments SQLAlchemy models."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Guid


class PaymentModel(Base):
    """SQLAlchemy model for Payment."""

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        {"comment": "Платежи по финансовым субъектам (поступления от владельцев)", "extend_existing": True},
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
