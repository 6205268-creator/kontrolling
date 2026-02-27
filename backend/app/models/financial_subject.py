from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Guid


def generate_financial_subject_code() -> str:
    """Генерация уникального кода для платёжных документов: FS-{short_uuid}."""
    return f"FS-{uuid.uuid4().hex[:8].upper()}"


class FinancialSubject(Base):
    """Финансовый субъект — центр финансовой ответственности.

    Ключевая концепция: все начисления (Accrual) и платежи (Payment)
    привязываются к FinancialSubject, а не напрямую к бизнес-объектам.
    Это позволяет единообразно работать с разными типами обязательств:
    - LAND_PLOT — земельный участок
    - WATER_METER — счётчик воды
    - ELECTRICITY_METER — счётчик электроэнергии
    - GENERAL_DECISION — решение общего собрания
    """

    __tablename__ = "financial_subjects"
    __table_args__ = (
        UniqueConstraint(
            "subject_type",
            "subject_id",
            "cooperative_id",
            name="uq_financial_subjects_type_subject_coop",
        ),
        {"comment": "Финансовые субъекты — центры финансовой ответственности (участки, счётчики, решения)"},
    )

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    subject_type: Mapped[str] = mapped_column(String(30), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(Guid(), nullable=False)
    cooperative_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cooperatives.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, default=generate_financial_subject_code)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    cooperative: Mapped["Cooperative"] = relationship("Cooperative", back_populates="financial_subjects")
    accruals: Mapped[list["Accrual"]] = relationship("Accrual", back_populates="financial_subject")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="financial_subject")
