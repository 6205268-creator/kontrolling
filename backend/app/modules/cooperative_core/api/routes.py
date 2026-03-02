"""FastAPI routes for cooperative_core module."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.modules.administration.domain.entities import AppUser

from .schemas import CooperativeCreate, CooperativeInDB, CooperativeUpdate
from ..infrastructure.repositories import CooperativeRepository
from ..application.use_cases import (
    CreateCooperativeUseCase,
    GetCooperativeUseCase,
    GetCooperativesUseCase,
    UpdateCooperativeUseCase,
    DeleteCooperativeUseCase,
)

router = APIRouter()


def _get_cooperative_repo(db: AsyncSession) -> CooperativeRepository:
    """Get cooperative repository instance."""
    return CooperativeRepository(db)


@router.get(
    "/",
    response_model=list[CooperativeInDB],
    summary="Список СТ",
    description="Получить список садоводческих товариществ. Admin видит все СТ, chairman/treasurer — только своё.",
)
async def get_cooperatives(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> list[CooperativeInDB]:
    """
    Получить список Cooperative.

    - **admin**: видит все СТ
    - **chairman/treasurer**: видят только своё СТ
    """
    repo = _get_cooperative_repo(db)
    use_case = GetCooperativesUseCase(repo)
    
    cooperative_id = None if current_user.role == "admin" else current_user.cooperative_id
    cooperatives = await use_case.execute(cooperative_id=cooperative_id)
    
    # Apply pagination after fetching
    return cooperatives[skip : skip + limit]


@router.get(
    "/{cooperative_id}",
    response_model=CooperativeInDB,
    summary="Получить СТ",
    description="Получить информацию о садоводческом товариществе по ID. Admin видит все, остальные — только своё.",
)
async def get_cooperative(
    cooperative_id: UUID,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> CooperativeInDB:
    """Получить Cooperative по ID."""
    # Проверка доступа: admin видит все, остальные только своё
    if current_user.role != "admin" and current_user.cooperative_id != cooperative_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к данному СТ",
        )

    repo = _get_cooperative_repo(db)
    use_case = GetCooperativeUseCase(repo)
    
    cooperative = await use_case.execute(
        cooperative_id=cooperative_id,
        current_cooperative_id=current_user.cooperative_id,
    )
    
    if cooperative is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="СТ не найдено",
        )
    return cooperative


@router.post(
    "/",
    response_model=CooperativeInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Создать СТ",
    description="Создать новое садоводческое товарищество. Доступно только admin.",
)
async def create_cooperative(
    cooperative_data: CooperativeCreate,
    _: Annotated[AppUser, Depends(require_role(["admin"]))],
    db: AsyncSession = Depends(get_db),
) -> CooperativeInDB:
    """Создать новое СТ (только admin)."""
    repo = _get_cooperative_repo(db)
    use_case = CreateCooperativeUseCase(repo)
    
    cooperative = await use_case.execute(data=cooperative_data)
    return cooperative


@router.patch(
    "/{cooperative_id}",
    response_model=CooperativeInDB,
    summary="Обновить СТ",
    description="Обновить информацию о садоводческом товариществе. Доступно только admin.",
)
async def update_cooperative(
    cooperative_id: UUID,
    cooperative_data: CooperativeUpdate,
    _: Annotated[AppUser, Depends(require_role(["admin"]))],
    db: AsyncSession = Depends(get_db),
) -> CooperativeInDB:
    """Обновить СТ (только admin)."""
    repo = _get_cooperative_repo(db)
    use_case = UpdateCooperativeUseCase(repo)
    
    cooperative = await use_case.execute(
        cooperative_id=cooperative_id,
        data=cooperative_data,
        current_cooperative_id=cooperative_id,  # admin operation
    )
    
    if cooperative is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="СТ не найдено",
        )
    return cooperative


@router.delete(
    "/{cooperative_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить СТ",
    description="Удалить садоводческое товарищество. Доступно только admin.",
)
async def delete_cooperative(
    cooperative_id: UUID,
    _: Annotated[AppUser, Depends(require_role(["admin"]))],
    db: AsyncSession = Depends(get_db),
) -> None:
    """Удалить СТ (только admin)."""
    repo = _get_cooperative_repo(db)
    use_case = DeleteCooperativeUseCase(repo)
    
    deleted = await use_case.execute(
        cooperative_id=cooperative_id,
        current_cooperative_id=cooperative_id,  # admin operation
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="СТ не найдено",
        )
