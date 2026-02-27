from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.app_user import AppUser
from app.schemas.owner import OwnerCreate, OwnerInDB, OwnerUpdate
from app.services import owner_service

router = APIRouter()


@router.get(
    "/",
    response_model=list[OwnerInDB],
    summary="Список владельцев",
    description="Получить список всех владельцев (физических и юридических лиц).",
)
async def get_owners(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> list[OwnerInDB]:
    """Получить список владельцев."""
    owners = await owner_service.get_owners(db=db, skip=skip, limit=limit)
    return owners


@router.get(
    "/search",
    response_model=list[OwnerInDB],
    summary="Поиск владельцев",
    description="Поиск владельцев по имени или УНП (налоговый номер).",
)
async def search_owners(
    q: Annotated[str, Query(description="Поисковый запрос (имя или УНП)")],
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
) -> list[OwnerInDB]:
    """Поиск владельцев по имени или tax_id."""
    owners = await owner_service.search_owners(db=db, query=q, limit=limit)
    return owners


@router.get(
    "/{owner_id}",
    response_model=OwnerInDB,
    summary="Получить владельца",
    description="Получить информацию о владельце по ID.",
)
async def get_owner(
    owner_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> OwnerInDB:
    """Получить владельца по ID."""
    owner = await owner_service.get_owner(db, owner_id)
    if owner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Владелец не найден",
        )
    return owner


@router.post(
    "/",
    response_model=OwnerInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Создать владельца",
    description="Создать нового владельца (физическое или юридическое лицо). Доступно: treasurer, admin.",
)
async def create_owner(
    owner_data: OwnerCreate,
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    db: AsyncSession = Depends(get_db),
) -> OwnerInDB:
    """Создать нового владельца (treasurer, admin)."""
    owner = await owner_service.create_owner(db, owner_data)
    return owner


@router.patch(
    "/{owner_id}",
    response_model=OwnerInDB,
    summary="Обновить владельца",
    description="Обновить информацию о владельце. Доступно: treasurer, admin.",
)
async def update_owner(
    owner_id: UUID,
    owner_data: OwnerUpdate,
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    db: AsyncSession = Depends(get_db),
) -> OwnerInDB:
    """Обновить владельца (treasurer, admin)."""
    owner = await owner_service.update_owner(db, owner_id, owner_data)
    if owner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Владелец не найден",
        )
    return owner


@router.delete(
    "/{owner_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить владельца",
    description="Удалить владельца. Доступно только admin.",
)
async def delete_owner(
    owner_id: UUID,
    _: Annotated[AppUser, Depends(require_role(["admin"]))],
    db: AsyncSession = Depends(get_db),
) -> None:
    """Удалить владельца (только admin)."""
    deleted = await owner_service.delete_owner(db, owner_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Владелец не найден",
        )
