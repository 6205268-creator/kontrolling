from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ContributionTypeInDB(BaseModel):
    """Схема вида взноса для ответа API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="ID вида взноса")
    name: str = Field(..., description="Название")
    code: str = Field(..., description="Код")
    description: str | None = Field(None, description="Описание")
