"""Pydantic schemas for financial_core API."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.financial_core.application.dtos import (
    BalanceInfo,
    FinancialSubjectBase,
    FinancialSubjectCreate,
    FinancialSubjectInDB,
    FinancialSubjectInfo,
)

__all__ = [
    "BalanceInfo",
    "FinancialSubjectBase",
    "FinancialSubjectCreate",
    "FinancialSubjectInDB",
    "FinancialSubjectInfo",
    # Period schemas
    "FinancialPeriodCreate",
    "FinancialPeriodInDB",
    "FinancialPeriodClose",
    "FinancialPeriodReopen",
]


# =============================================================================
# Financial Period Schemas
# =============================================================================


class FinancialPeriodCreate(BaseModel):
    """Schema for creating a financial period."""

    period_type: str = Field(..., description="Тип периода: monthly или yearly")
    year: int = Field(..., ge=1900, le=2100, description="Год периода")
    month: int | None = Field(None, ge=1, le=12, description="Месяц (1-12) для monthly, None для yearly")


class FinancialPeriodInDB(BaseModel):
    """Schema for financial period with DB fields."""

    id: UUID
    cooperative_id: UUID
    period_type: str
    year: int
    month: int | None
    start_date: date
    end_date: date
    status: str
    closed_at: datetime | None
    closed_by_user_id: UUID | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FinancialPeriodClose(BaseModel):
    """Schema for closing a financial period."""

    pass  # No additional fields needed


class FinancialPeriodReopen(BaseModel):
    """Schema for reopening a financial period."""

    pass  # Authorization handled by user role
