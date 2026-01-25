from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class IdResponse(BaseModel):
    id: int


class Timestamped(BaseModel):
    created_at: datetime
    updated_at: Optional[datetime] = None


class DocumentBase(BaseModel):
    number: str
    date: date

