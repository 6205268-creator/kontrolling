"""AppUser SQLAlchemy model."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Guid


class AppUserModel(Base):
    """SQLAlchemy model for AppUser."""

    __tablename__ = "app_users"
    __table_args__ = {"comment": "Пользователи системы (администраторы, председатели, бухгалтеры)", "extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(Guid(), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    cooperative_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("cooperatives.id"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def to_domain(self) -> "AppUser":
        """Convert to domain entity."""
        from app.modules.administration.domain.entities import AppUser
        return AppUser(
            id=self.id,
            username=self.username,
            email=self.email,
            hashed_password=self.hashed_password,
            full_name=self.full_name,
            role=self.role,
            cooperative_id=self.cooperative_id,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, entity: "AppUser") -> "AppUserModel":
        """Create from domain entity."""
        return cls(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            hashed_password=entity.hashed_password,
            full_name=entity.full_name,
            role=entity.role,
            cooperative_id=entity.cooperative_id,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
