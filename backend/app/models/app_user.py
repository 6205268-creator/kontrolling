from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Guid


class AppUser(Base):
    """Пользователь системы — сотрудник СТ или администратор.

    Роли:
    - admin — системный администратор, доступ ко всем СТ
    - chairman — председатель СТ, просмотр данных своего СТ
    - treasurer — казначей СТ, операционная работа (начисления, платежи, расходы)

    Привязка к СТ через cooperative_id (для chairman и treasurer).
    """

    __tablename__ = "app_users"
    __table_args__ = {"comment": "Пользователи системы (администраторы, председатели, казначеи)"}

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="treasurer")
    cooperative_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("cooperatives.id"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        comment="Дата и время последнего обновления записи",
    )

    cooperative: Mapped["Cooperative | None"] = relationship("Cooperative", back_populates="users")
