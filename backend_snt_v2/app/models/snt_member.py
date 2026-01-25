from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SntMember(Base):
    __tablename__ = "snt_member"
    __table_args__ = (
        UniqueConstraint("snt_id", "physical_person_id", "date_from", name="uq_snt_member_snt_person_from"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snt_id: Mapped[int] = mapped_column(ForeignKey("snt.id", ondelete="RESTRICT"), nullable=False)
    physical_person_id: Mapped[int] = mapped_column(
        ForeignKey("physical_person.id", ondelete="RESTRICT"), nullable=False
    )
    date_from: Mapped[date] = mapped_column(Date, nullable=False)
    date_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
