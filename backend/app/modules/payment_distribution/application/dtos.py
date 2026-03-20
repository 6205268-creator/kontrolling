"""Payment Distribution application DTOs."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MemberInDB(BaseModel):
    """Schema for Member with DB fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    cooperative_id: UUID
    personal_account_id: UUID | None = None
    status: str
    joined_at: datetime | None
    created_at: datetime


class PersonalAccountInDB(BaseModel):
    """Schema for PersonalAccount with DB fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    member_id: UUID
    cooperative_id: UUID
    account_number: str
    balance: Decimal
    status: str
    opened_at: datetime
    closed_at: datetime | None


class PersonalAccountTransactionInDB(BaseModel):
    """Schema for PersonalAccountTransaction with DB fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    payment_id: UUID | None
    distribution_id: UUID | None
    transaction_number: str
    transaction_date: datetime
    amount: Decimal
    type: str  # credit, debit
    description: str | None


class PaymentDistributionInDB(BaseModel):
    """Schema for PaymentDistribution with DB fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    payment_id: UUID
    financial_subject_id: UUID
    accrual_id: UUID | None
    distribution_number: str
    distributed_at: datetime
    amount: Decimal
    priority: int
    status: str  # applied, reversed


class PersonalAccountBalance(BaseModel):
    """Schema for personal account balance info."""

    account_number: str
    balance: Decimal = Field(..., description="Текущий баланс")
    status: str
    last_transaction_date: datetime | None = None


class PaymentDistributionResult(BaseModel):
    """Schema for payment distribution result."""

    payment_id: UUID
    total_distributed: Decimal
    remaining_balance: Decimal
    distributions: list[PaymentDistributionInDB]
