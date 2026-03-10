"""Financial Core SQLAlchemy models.

SQLAlchemy ORM models for database operations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Guid


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
            subject_type=self.subject_type,
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
