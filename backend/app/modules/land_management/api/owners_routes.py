"""API routes for owners — exposed at /api/owners for frontend compatibility."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.modules.administration.domain.entities import AppUser
from app.modules.deps import (
    get_create_owner_use_case,
    get_delete_owner_use_case,
    get_get_owner_use_case,
    get_get_owners_use_case,
    get_search_owners_use_case,
    get_update_owner_use_case,
)

from .schemas import OwnerCreate, OwnerInDB, OwnerUpdate

router = APIRouter()


@router.get(
    "/",
    response_model=list[OwnerInDB],
    summary="Список владельцев",
    description="Получить список всех владельцев (физических и юридических лиц).",
)
async def get_owners(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_get_owners_use_case),
    skip: int = 0,
    limit: int = 100,
) -> list[OwnerInDB]:
    """Получить список владельцев."""
    owners = await use_case.execute(skip=skip, limit=limit)
    return [
        OwnerInDB(
            id=o.id,
            owner_type=o.owner_type,
            name=o.name,
            tax_id=o.tax_id,
            contact_phone=o.contact_phone,
            contact_email=o.contact_email,
            created_at=o.created_at,
            updated_at=o.updated_at,
        )
        for o in owners
    ]


@router.get(
    "/search",
    response_model=list[OwnerInDB],
    summary="Поиск владельцев",
    description="Поиск владельцев по имени или УНП (налоговый номер).",
)
async def search_owners(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    q: Annotated[str, Query(description="Поисковый запрос (имя или УНП)")],
    use_case=Depends(get_search_owners_use_case),
    limit: int = 100,
) -> list[OwnerInDB]:
    """Поиск владельцев по имени или tax_id."""
    owners = await use_case.execute(query=q, limit=limit)
    return [
        OwnerInDB(
            id=o.id,
            owner_type=o.owner_type,
            name=o.name,
            tax_id=o.tax_id,
            contact_phone=o.contact_phone,
            contact_email=o.contact_email,
            created_at=o.created_at,
            updated_at=o.updated_at,
        )
        for o in owners
    ]


@router.get(
    "/{owner_id}",
    response_model=OwnerInDB,
    summary="Получить владельца",
    description="Получить информацию о владельце по ID.",
)
async def get_owner(
    owner_id: UUID,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_get_owner_use_case),
) -> OwnerInDB:
    """Получить владельца по ID."""
    owner = await use_case.execute(owner_id=owner_id)

    if owner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Владелец не найден",
        )
    return OwnerInDB(
        id=owner.id,
        owner_type=owner.owner_type,
        name=owner.name,
        tax_id=owner.tax_id,
        contact_phone=owner.contact_phone,
        contact_email=owner.contact_email,
        created_at=owner.created_at,
        updated_at=owner.updated_at,
    )


@router.post(
    "/",
    response_model=OwnerInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Создать владельца",
    description="Создать нового владельца (физическое или юридическое лицо). Доступно: treasurer, admin.",
)
async def create_owner(
    owner_data: OwnerCreate,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_create_owner_use_case),
) -> OwnerInDB:
    """Создать нового владельца (treasurer, admin)."""
    owner = await use_case.execute(data=owner_data)

    return OwnerInDB(
        id=owner.id,
        owner_type=owner.owner_type,
        name=owner.name,
        tax_id=owner.tax_id,
        contact_phone=owner.contact_phone,
        contact_email=owner.contact_email,
        created_at=owner.created_at,
        updated_at=owner.updated_at,
    )


@router.patch(
    "/{owner_id}",
    response_model=OwnerInDB,
    summary="Обновить владельца",
    description="Обновить информацию о владельце. Доступно: treasurer, admin.",
)
async def update_owner(
    owner_id: UUID,
    owner_data: OwnerUpdate,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_update_owner_use_case),
) -> OwnerInDB:
    """Обновить владельца (treasurer, admin)."""
    owner = await use_case.execute(owner_id=owner_id, data=owner_data)

    if owner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Владелец не найден",
        )
    return OwnerInDB(
        id=owner.id,
        owner_type=owner.owner_type,
        name=owner.name,
        tax_id=owner.tax_id,
        contact_phone=owner.contact_phone,
        contact_email=owner.contact_email,
        created_at=owner.created_at,
        updated_at=owner.updated_at,
    )


@router.delete(
    "/{owner_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить владельца",
    description="Удалить владельца. Доступно только admin.",
)
async def delete_owner(
    owner_id: UUID,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_delete_owner_use_case),
) -> None:
    """Удалить владельца (только admin)."""
    deleted = await use_case.execute(owner_id=owner_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Владелец не найден",
        )
