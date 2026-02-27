from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OwnerBase(BaseModel):
    """Базовая схема Owner."""

    owner_type: str = Field(..., description="Тип владельца", pattern="^(physical|legal)$")
    name: str = Field(..., description="ФИО или название организации", min_length=1, max_length=255)
    tax_id: str | None = Field(None, description="УНП/ИД", max_length=20)
    contact_phone: str | None = Field(None, description="Телефон", max_length=50)
    contact_email: str | None = Field(None, description="Email", max_length=255)


class OwnerCreate(OwnerBase):
    """Схема для создания Owner."""

    pass


class OwnerUpdate(BaseModel):
    """Схема для обновления Owner."""

    owner_type: str | None = Field(None, description="Тип владельца", pattern="^(physical|legal)$")
    name: str | None = Field(None, description="ФИО или название организации", min_length=1, max_length=255)
    tax_id: str | None = Field(None, description="УНП/ИД", max_length=20)
    contact_phone: str | None = Field(None, description="Телефон", max_length=50)
    contact_email: str | None = Field(None, description="Email", max_length=255)


class OwnerInDB(OwnerBase):
    """Схема Owner с полями БД."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
