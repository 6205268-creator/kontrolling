from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Guid


class ContributionType(Base):
    """Вид взноса — справочник типов начислений.

    Используется для классификации начислений (Accrual):
    - Членский взнос — регулярные платежи членов СТ
    - Целевой взнос — на конкретные цели (ремонт, благоустройство)
    - Взнос за электричество — оплата электроэнергии
    - Взнос за воду — оплата водоснабжения
    - Другие виды взносов
    """

    __tablename__ = "contribution_types"
    __table_args__ = {"comment": "Справочник видов взносов (членский, целевой, за услуги)"}

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    accruals: Mapped[list["Accrual"]] = relationship("Accrual", back_populates="contribution_type")
