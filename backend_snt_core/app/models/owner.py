from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Owner(Base):
    __tablename__ = "owner"
    __table_args__ = (
        UniqueConstraint("snt_id", "full_name", name="uq_owner_snt_full_name"),
        UniqueConstraint("snt_id", "id", name="uq_owner_snt_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snt_id: Mapped[int] = mapped_column(ForeignKey("snt.id", ondelete="RESTRICT"), nullable=False)

    full_name: Mapped[str] = mapped_column(String(250), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

