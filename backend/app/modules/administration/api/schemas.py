"""Pydantic schemas for administration API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base schema for AppUser."""

    email: EmailStr = Field(..., description="Email")
    full_name: str | None = Field(None, description="ФИО", max_length=255)
    role: str = Field("user", description="Роль", pattern="^(admin|chairman|treasurer|user)$")
    cooperative_id: UUID | None = Field(None, description="ID СТ")


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., description="Пароль", min_length=6)


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    full_name: str | None = Field(None, description="ФИО", max_length=255)
    role: str | None = Field(None, description="Роль", pattern="^(admin|chairman|treasurer|user)$")
    cooperative_id: UUID | None = Field(None, description="ID СТ")


class UserInDB(UserBase):
    """Schema for AppUser with DB fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for JWT token payload."""

    email: str | None = None
    cooperative_id: UUID | None = None
    role: str | None = None
