"""FastAPI routes for contribution types."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.modules.administration.domain.entities import AppUser

from ..infrastructure.repositories import ContributionTypeRepository
from ..application.use_cases import GetContributionTypesUseCase
from .schemas import ContributionTypeInDB

router = APIRouter()


def _get_contribution_type_repo(db: AsyncSession) -> ContributionTypeRepository:
    """Get contribution type repository instance."""
    return ContributionTypeRepository(db)


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
    repo = _get_contribution_type_repo(db)
    use_case = GetContributionTypesUseCase(repo)
    types_list = await use_case.execute()
    
    return [
        ContributionTypeInDB(
            id=t.id,
            name=t.name,
            code=t.code,
            description=t.description,
        )
        for t in types_list
    ]
