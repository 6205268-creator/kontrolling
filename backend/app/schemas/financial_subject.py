from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FinancialSubjectBase(BaseModel):
    """Базовая схема FinancialSubject."""

    subject_type: str = Field(
        ...,
        description="Тип субъекта",
        pattern="^(LAND_PLOT|WATER_METER|ELECTRICITY_METER|GENERAL_DECISION)$",
    )
    subject_id: UUID = Field(..., description="ID бизнес-объекта")
    cooperative_id: UUID = Field(..., description="ID coopérative")
    code: str = Field(..., description="Уникальный код", min_length=1, max_length=50)
    status: str = Field("active", description="Статус", pattern="^(active|closed)$")


class FinancialSubjectCreate(FinancialSubjectBase):
    """Схема для создания FinancialSubject."""

    pass


class FinancialSubjectInDB(FinancialSubjectBase):
    """Схема FinancialSubject с полями БД."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
