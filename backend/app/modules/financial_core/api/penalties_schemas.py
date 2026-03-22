"""Схемы API пеней и настроек."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PenaltyCalcRowOut(BaseModel):
    debt_line_id: UUID
    financial_subject_id: UUID
    outstanding: Decimal = Field(..., decimal_places=2)
    overdue_days: int
    penalty_amount: Decimal = Field(..., decimal_places=2)
    contribution_type_id: UUID


class PenaltySettingsCreate(BaseModel):
    contribution_type_id: UUID | None = Field(None, description="NULL — все виды взносов")
    is_enabled: bool = True
    daily_rate: Decimal = Field(..., description="Доля в день, напр. 0.0003 = 0.03%")
    grace_period_days: int = Field(10, ge=0, le=365)
    effective_from: date
    effective_to: date | None = None


class PenaltySettingsUpdate(BaseModel):
    contribution_type_id: UUID | None = None
    is_enabled: bool | None = None
    daily_rate: Decimal | None = None
    grace_period_days: int | None = Field(None, ge=0, le=365)
    effective_from: date | None = None
    effective_to: date | None = None


class PenaltySettingsOut(BaseModel):
    id: UUID
    cooperative_id: UUID
    contribution_type_id: UUID | None
    is_enabled: bool
    daily_rate: Decimal
    grace_period_days: int
    effective_from: date
    effective_to: date | None


class WriteOffPenaltyBody(BaseModel):
    reason: str | None = Field(None, max_length=500)
