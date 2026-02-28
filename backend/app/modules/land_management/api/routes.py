"""FastAPI routes for land_management module."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.app_user import AppUser
from app.modules.shared.kernel.events import EventDispatcher

from .schemas import (
    LandPlotCreate,
    LandPlotUpdate,
    LandPlotWithOwners,
    OwnerCreate,
    OwnerInDB,
    OwnerUpdate,
    PlotOwnershipCreate,
    PlotOwnershipInDB,
)
from ..infrastructure.repositories import (
    LandPlotRepository,
    OwnerRepository,
    PlotOwnershipRepository,
)
from ..application.use_cases import (
    CreateLandPlotUseCase,
    GetLandPlotUseCase,
    GetLandPlotsUseCase,
    UpdateLandPlotUseCase,
    DeleteLandPlotUseCase,
    CreateOwnerUseCase,
    GetOwnerUseCase,
    GetOwnersUseCase,
    UpdateOwnerUseCase,
    DeleteOwnerUseCase,
    SearchOwnersUseCase,
    CreatePlotOwnershipUseCase,
    ClosePlotOwnershipUseCase,
    GetPlotOwnershipUseCase,
    GetCurrentPlotOwnershipsUseCase,
)

router = APIRouter()

# Global event dispatcher instance
_event_dispatcher = EventDispatcher()


def _get_land_plot_repo(db: AsyncSession) -> LandPlotRepository:
    """Get land plot repository instance."""
    return LandPlotRepository(db)


def _get_owner_repo(db: AsyncSession) -> OwnerRepository:
    """Get owner repository instance."""
    return OwnerRepository(db)


def _get_ownership_repo(db: AsyncSession) -> PlotOwnershipRepository:
    """Get plot ownership repository instance."""
    return PlotOwnershipRepository(db)


def _get_event_dispatcher() -> EventDispatcher:
    """Get event dispatcher instance."""
    return _event_dispatcher


@router.get(
    "/",
    response_model=list[LandPlotWithOwners],
    summary="Список участков",
    description="Получить список земельных участков. Admin видит все, chairman/treasurer — только своё СТ.",
)
async def get_land_plots(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    cooperative_id: UUID | None = Query(None, description="Фильтр по СТ"),
    skip: int = 0,
    limit: int = 100,
) -> list[LandPlotWithOwners]:
    """
    Получить список участков.

    - **admin**: может указать cooperative_id или получить все
    - **chairman/treasurer**: видят только участки своего СТ
    """
    # Для не-admin пользователей используем их СТ
    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id

    if cooperative_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cooperative_id is required for non-admin users",
        )

    repo = _get_land_plot_repo(db)
    use_case = GetLandPlotsUseCase(repo)
    plots = await use_case.execute(cooperative_id=cooperative_id, skip=skip, limit=limit)

    # For now, return basic list without owners/financial subject details
    # This would need a separate use case to fetch owners and financial subjects
    return [
        LandPlotWithOwners(
            id=plot.id,
            cooperative_id=plot.cooperative_id,
            plot_number=plot.plot_number,
            area_sqm=plot.area_sqm,
            cadastral_number=plot.cadastral_number,
            status=plot.status,
            created_at=plot.created_at,
            updated_at=plot.updated_at,
            owners=[],
            financial_subject_id=None,
            financial_subject_code=None,
        )
        for plot in plots
    ]


@router.get(
    "/{plot_id}",
    response_model=LandPlotWithOwners,
    summary="Получить участок",
    description="Получить информацию об участке по ID с владельцами и финансовым субъектом.",
)
async def get_land_plot(
    plot_id: UUID,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> LandPlotWithOwners:
    """Получить участок по ID с владельцами и финансовым субъектом."""
    repo = _get_land_plot_repo(db)
    use_case = GetLandPlotUseCase(repo)
    
    plot = await use_case.execute(plot_id=plot_id, cooperative_id=current_user.cooperative_id)
    
    if plot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Участок не найден",
        )

    # Проверка доступа: admin видит все, остальные только своё СТ
    if current_user.role != "admin" and current_user.cooperative_id != plot.cooperative_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к данному участку",
        )

    # Get current ownerships
    ownership_repo = _get_ownership_repo(db)
    ownerships_use_case = GetCurrentPlotOwnershipsUseCase(ownership_repo)
    ownerships = await ownerships_use_case.execute(plot_id)

    return LandPlotWithOwners(
        id=plot.id,
        cooperative_id=plot.cooperative_id,
        plot_number=plot.plot_number,
        area_sqm=plot.area_sqm,
        cadastral_number=plot.cadastral_number,
        status=plot.status,
        created_at=plot.created_at,
        updated_at=plot.updated_at,
        owners=[
            PlotOwnershipInDB(
                id=o.id,
                land_plot_id=o.land_plot_id,
                owner_id=o.owner_id,
                share_numerator=o.share_numerator,
                share_denominator=o.share_denominator,
                is_primary=o.is_primary,
                valid_from=o.valid_from,
                valid_to=o.valid_to,
                created_at=o.created_at,
                updated_at=o.updated_at,
            )
            for o in ownerships
        ],
        financial_subject_id=None,  # Would need to query financial_core
        financial_subject_code=None,
    )


@router.post(
    "/",
    response_model=LandPlotWithOwners,
    status_code=status.HTTP_201_CREATED,
    summary="Создать участок",
    description="Создать новый земельный участок с владельцами. Автоматически создаётся FinancialSubject. Доступно: treasurer, admin.",
)
async def create_land_plot(
    plot_data: LandPlotCreate,
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    db: AsyncSession = Depends(get_db),
) -> LandPlotWithOwners:
    """Создать участок с владельцами (treasurer, admin)."""
    # Override cooperative_id with user's cooperative for non-admin
    if current_user.role != "admin":
        plot_data.cooperative_id = current_user.cooperative_id

    land_plot_repo = _get_land_plot_repo(db)
    ownership_repo = _get_ownership_repo(db)
    event_dispatcher = _get_event_dispatcher()
    
    use_case = CreateLandPlotUseCase(land_plot_repo, ownership_repo, event_dispatcher)
    plot = await use_case.execute(data=plot_data, ownerships=plot_data.ownerships)

    return LandPlotWithOwners(
        id=plot.id,
        cooperative_id=plot.cooperative_id,
        plot_number=plot.plot_number,
        area_sqm=plot.area_sqm,
        cadastral_number=plot.cadastral_number,
        status=plot.status,
        created_at=plot.created_at,
        updated_at=plot.updated_at,
        owners=[],
        financial_subject_id=None,
        financial_subject_code=None,
    )


@router.patch(
    "/{plot_id}",
    response_model=LandPlotWithOwners,
    summary="Обновить участок",
    description="Обновить информацию об участке. Доступно: treasurer, admin.",
)
async def update_land_plot(
    plot_id: UUID,
    plot_data: LandPlotUpdate,
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    db: AsyncSession = Depends(get_db),
) -> LandPlotWithOwners:
    """Обновить участок (treasurer, admin)."""
    repo = _get_land_plot_repo(db)
    use_case = UpdateLandPlotUseCase(repo)
    
    plot = await use_case.execute(
        plot_id=plot_id,
        data=plot_data,
        cooperative_id=current_user.cooperative_id,
    )
    
    if plot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Участок не найден",
        )

    return LandPlotWithOwners(
        id=plot.id,
        cooperative_id=plot.cooperative_id,
        plot_number=plot.plot_number,
        area_sqm=plot.area_sqm,
        cadastral_number=plot.cadastral_number,
        status=plot.status,
        created_at=plot.created_at,
        updated_at=plot.updated_at,
        owners=[],
        financial_subject_id=None,
        financial_subject_code=None,
    )


@router.delete(
    "/{plot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить участок",
    description="Удалить земельный участок. Доступно только admin.",
)
async def delete_land_plot(
    plot_id: UUID,
    _: Annotated[AppUser, Depends(require_role(["admin"]))],
    db: AsyncSession = Depends(get_db),
) -> None:
    """Удалить участок (только admin)."""
    repo = _get_land_plot_repo(db)
    use_case = DeleteLandPlotUseCase(repo)
    
    deleted = await use_case.execute(plot_id=plot_id, cooperative_id=_.cooperative_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Участок не найден",
        )


@router.get(
    "/owners/",
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
    repo = _get_owner_repo(db)
    use_case = GetOwnersUseCase(repo)
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
    "/owners/search",
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
    repo = _get_owner_repo(db)
    use_case = SearchOwnersUseCase(repo)
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
    "/owners/{owner_id}",
    response_model=OwnerInDB,
    summary="Получить владельца",
    description="Получить информацию о владельце по ID.",
)
async def get_owner(
    owner_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> OwnerInDB:
    """Получить владельца по ID."""
    repo = _get_owner_repo(db)
    use_case = GetOwnerUseCase(repo)
    
    owner = await use_case.execute(owner_id=owner_id)
    
    if owner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Владелец не найден",
        )
    return owner


@router.post(
    "/owners/",
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
    repo = _get_owner_repo(db)
    event_dispatcher = _get_event_dispatcher()
    use_case = CreateOwnerUseCase(repo, event_dispatcher)
    
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
    "/owners/{owner_id}",
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
    repo = _get_owner_repo(db)
    use_case = UpdateOwnerUseCase(repo)
    
    owner = await use_case.execute(owner_id=owner_id, data=owner_data)
    
    if owner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Владелец не найден",
        )
    return owner


@router.delete(
    "/owners/{owner_id}",
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
    repo = _get_owner_repo(db)
    use_case = DeleteOwnerUseCase(repo)
    
    deleted = await use_case.execute(owner_id=owner_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Владелец не найден",
        )


@router.post(
    "/{plot_id}/ownerships",
    response_model=PlotOwnershipInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить владельца к участку",
    description="Добавить право собственности (владельца) к участку с указанием доли. Доступно: treasurer, admin.",
)
async def add_ownership(
    plot_id: UUID,
    ownership_data: PlotOwnershipCreate,
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    db: AsyncSession = Depends(get_db),
) -> PlotOwnershipInDB:
    """Добавить владельца к участку (treasurer, admin)."""
    land_plot_repo = _get_land_plot_repo(db)
    ownership_repo = _get_ownership_repo(db)
    event_dispatcher = _get_event_dispatcher()
    
    use_case = CreatePlotOwnershipUseCase(ownership_repo, land_plot_repo, event_dispatcher)
    
    ownership = await use_case.execute(
        land_plot_id=plot_id,
        data=ownership_data,
        cooperative_id=current_user.cooperative_id,
    )
    
    return PlotOwnershipInDB(
        id=ownership.id,
        land_plot_id=ownership.land_plot_id,
        owner_id=ownership.owner_id,
        share_numerator=ownership.share_numerator,
        share_denominator=ownership.share_denominator,
        is_primary=ownership.is_primary,
        valid_from=ownership.valid_from,
        valid_to=ownership.valid_to,
        created_at=ownership.created_at,
        updated_at=ownership.updated_at,
    )


@router.patch(
    "/ownerships/{ownership_id}/close",
    response_model=PlotOwnershipInDB,
    summary="Закрыть право собственности",
    description="Закрыть право собственности на участок (установить дату прекращения valid_to). Доступно: treasurer, admin.",
)
async def close_ownership(
    ownership_id: UUID,
    valid_to: date = Query(..., description="Дата прекращения владения"),
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))] = None,
    db: AsyncSession = Depends(get_db),
) -> PlotOwnershipInDB:
    """Закрыть право собственности (установить valid_to) (treasurer, admin)."""
    ownership_repo = _get_ownership_repo(db)
    event_dispatcher = _get_event_dispatcher()
    
    use_case = ClosePlotOwnershipUseCase(ownership_repo, event_dispatcher)
    
    ownership = await use_case.execute(
        ownership_id=ownership_id,
        valid_to=valid_to,
        cooperative_id=current_user.cooperative_id,  # type: ignore[union-attr]
    )
    
    if ownership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Право собственности не найдено",
        )
    
    return ownership
