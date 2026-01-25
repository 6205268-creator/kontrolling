from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class AccrualRowCreate(BaseModel):
    plot_id: int
    charge_item_id: int
    owner_id: int
    amount: Decimal = Field(gt=0)
    period_from: Optional[date] = None
    period_to: Optional[date] = None


class AccrualCreate(BaseModel):
    number: str
    date: date
    rows: List[AccrualRowCreate]


class AccrualRead(BaseModel):
    id: int
    snt_id: int
    number: str
    date: date
    is_posted: bool


class PaymentRowCreate(BaseModel):
    plot_id: int
    owner_id: int
    charge_item_id: int
    amount: Decimal = Field(gt=0)


class PaymentCreate(BaseModel):
    number: str
    date: date
    rows: List[PaymentRowCreate]


class PaymentRead(BaseModel):
    id: int
    snt_id: int
    number: str
    date: date
    is_posted: bool

