from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.app_user import AppUser
from app.models.contribution_type import ContributionType
from app.schemas.contribution_type import ContributionTypeInDB

router = APIRouter()


@router.get(
    "/",
    response_model=list[ContributionTypeInDB],
    summary="Справочник видов взносов",
    description="Получить список видов взносов (Членский, Целевой и т.д.) для использования в формах начислений.",
)
async def get_contribution_types(
    _: Annotated[AppUser, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> list[ContributionTypeInDB]:
    """Получить справочник видов взносов (для форм начислений)."""
    result = await db.execute(select(ContributionType).order_by(ContributionType.name))
    types_list = result.scalars().all()
    return [ContributionTypeInDB.model_validate(t) for t in types_list]
