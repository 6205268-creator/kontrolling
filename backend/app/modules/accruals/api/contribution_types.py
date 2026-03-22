"""FastAPI routes for contribution types."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.modules.administration.domain.entities import AppUser
from app.modules.deps import get_get_contribution_types_use_case

from .schemas import ContributionTypeInDB

router = APIRouter()


@router.get(
    "/",
    response_model=list[ContributionTypeInDB],
    summary="Справочник видов взносов",
    description="Получить список видов взносов (Членский, Целевой и т.д.) для использования в формах начислений.",
)
async def get_contribution_types(
    _: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_get_contribution_types_use_case),
) -> list[ContributionTypeInDB]:
    """Получить справочник видов взносов (для форм начислений)."""
    types_list = await use_case.execute()

    return [
        ContributionTypeInDB(
            id=t.id,
            name=t.name,
            code=t.code,
            description=t.description,
            is_system=t.is_system,
        )
        for t in types_list
    ]
