from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.app_user import AppUser
from app.schemas.land_plot import LandPlotCreate, LandPlotUpdate, LandPlotWithOwners
from app.schemas.plot_ownership import PlotOwnershipCreate, PlotOwnershipInDB
from app.services import land_plot_service

router = APIRouter()


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

    plots = await land_plot_service.get_land_plots_by_cooperative(
        db=db,
        cooperative_id=cooperative_id,  # type: ignore[arg-type]
        skip=skip,
        limit=limit,
    )

    # Формируем ответ с владельцами и финансовыми субъектами
    result = []
    for plot in plots:
        data = await land_plot_service.get_land_plot_with_owners(db, plot.id)
        if data:
            result.append(_build_land_plot_with_owners(plot, data["owners"], data["financial_subject"]))

    return result


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
    data = await land_plot_service.get_land_plot_with_owners(db, plot_id)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Участок не найден",
        )

    # Проверка доступа: admin видит все, остальные только своё СТ
    if current_user.role != "admin":
        if current_user.cooperative_id != data["plot"].cooperative_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет доступа к данному участку",
            )

    return _build_land_plot_with_owners(data["plot"], data["owners"], data["financial_subject"])


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
    plot = await land_plot_service.create_land_plot(db, plot_data, plot_data.ownerships)

    data = await land_plot_service.get_land_plot_with_owners(db, plot.id)
    return _build_land_plot_with_owners(data["plot"], data["owners"], data["financial_subject"])


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
    plot = await land_plot_service.update_land_plot(db, plot_id, plot_data)
    if plot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Участок не найден",
        )

    data = await land_plot_service.get_land_plot_with_owners(db, plot_id)
    return _build_land_plot_with_owners(data["plot"], data["owners"], data["financial_subject"])


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
    deleted = await land_plot_service.delete_land_plot(db, plot_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Участок не найден",
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
    # Проверка что участок существует
    plot = await land_plot_service.get_land_plot(db, plot_id)
    if plot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Участок не найден",
        )

    # Проверка доступа
    if current_user.role != "admin" and current_user.cooperative_id != plot.cooperative_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к данному участку",
        )

    ownership = await land_plot_service.add_plot_ownership(db, ownership_data)
    return ownership


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
    ownership = await land_plot_service.close_plot_ownership(db, ownership_id, valid_to)
    if ownership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Право собственности не найдено",
        )
    return ownership


def _build_land_plot_with_owners(
    plot: LandPlot,
    owners: list,
    financial_subject,
) -> LandPlotWithOwners:
    """Построение ответа LandPlotWithOwners из модели и данных."""
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
            for o in owners
        ],
        financial_subject_id=financial_subject.id if financial_subject else None,
        financial_subject_code=financial_subject.code if financial_subject else None,
    )
