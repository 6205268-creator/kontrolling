"""DTOs for payments application layer."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PaymentBase(BaseModel):
    """Base schema for Payment."""

    financial_subject_id: UUID = Field(..., description="ID финансового субъекта")
    payer_owner_id: UUID = Field(..., description="ID владельца (плательщика)")
    amount: Decimal = Field(..., description="Сумма платежа", gt=0, decimal_places=2)
    payment_date: date = Field(..., description="Дата платежа")
    document_number: str | None = Field(None, description="Номер документа", max_length=50)
    description: str | None = Field(None, description="Описание", max_length=512)


class PaymentCreate(PaymentBase):
    """Schema for creating a Payment."""

    pass


class PaymentUpdate(BaseModel):
    """Schema for updating a Payment."""

    document_number: str | None = Field(None, description="Номер документа", max_length=50)
    description: str | None = Field(None, description="Описание", max_length=512)


class PaymentInDB(PaymentBase):
    """Schema for Payment with DB fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str = Field(..., description="Статус (confirmed, cancelled)")
    created_at: datetime
    updated_at: datetime
