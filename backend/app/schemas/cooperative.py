from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CooperativeBase(BaseModel):
    """Базовая схема Cooperative."""

    name: str = Field(..., description="Название СТ", min_length=1, max_length=255)
    unp: str | None = Field(None, description="УНП", max_length=20)
    address: str | None = Field(None, description="Адрес", max_length=512)


class CooperativeCreate(CooperativeBase):
    """Схема для создания Cooperative."""

    pass


class CooperativeUpdate(BaseModel):
    """Схема для обновления Cooperative."""

    name: str | None = Field(None, description="Название СТ", min_length=1, max_length=255)
    unp: str | None = Field(None, description="УНП", max_length=20)
    address: str | None = Field(None, description="Адрес", max_length=512)


class CooperativeInDB(CooperativeBase):
    """Схема Cooperative с полями БД."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
