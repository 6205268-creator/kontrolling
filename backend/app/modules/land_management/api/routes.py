"""FastAPI routes for land_management module."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.modules.administration.domain.entities import AppUser
from app.modules.deps import (
    get_close_plot_ownership_use_case,
    get_create_land_plot_use_case,
    get_create_plot_ownership_use_case,
    get_current_plot_ownerships_use_case,
    get_delete_land_plot_use_case,
    get_get_land_plot_use_case,
    get_get_land_plots_use_case,
    get_get_owner_use_case,
    get_update_land_plot_use_case,
)

from .schemas import (
    LandPlotCreate,
    LandPlotUpdate,
    LandPlotWithOwners,
    PlotOwnershipCreate,
    PlotOwnershipInDB,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=list[LandPlotWithOwners],
    summary="Список участков",
    description="Получить список земельных участков. Admin видит все, chairman/treasurer — только своё СТ.",
)
async def get_land_plots(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_get_land_plots_use_case),
    get_ownerships_use_case=Depends(get_current_plot_ownerships_use_case),
    get_owner_use_case=Depends(get_get_owner_use_case),
    cooperative_id: UUID | None = Query(None, description="Фильтр по СТ"),
    skip: int = 0,
    limit: int = 100,
) -> list[LandPlotWithOwners]:
    """
    Получить список участков с владельцами (ФИО и доля).

    - **admin**: может указать cooperative_id или получить все
    - **chairman/treasurer**: видят только участки своего СТ
    """
    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id

    if cooperative_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cooperative_id is required for non-admin users",
        )

    plots = await use_case.execute(cooperative_id=cooperative_id, skip=skip, limit=limit)
    result = []
    for plot in plots:
        ownerships = await get_ownerships_use_case.execute(plot.id)
        owners_payload = []
        for o in ownerships:
            owner = await get_owner_use_case.execute(owner_id=o.owner_id)
            owner_name = owner.name if owner else "—"
            owners_payload.append(
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
                    owner_name=owner_name,
                )
            )
        result.append(
            LandPlotWithOwners(
                id=plot.id,
                cooperative_id=plot.cooperative_id,
                plot_number=plot.plot_number,
                area_sqm=plot.area_sqm,
                cadastral_number=plot.cadastral_number,
                status=plot.status,
                created_at=plot.created_at,
                updated_at=plot.updated_at,
                owners=owners_payload,
                financial_subject_id=None,
                financial_subject_code=None,
            )
        )
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
    get_plot_use_case=Depends(get_get_land_plot_use_case),
    get_ownerships_use_case=Depends(get_current_plot_ownerships_use_case),
    get_owner_use_case=Depends(get_get_owner_use_case),
) -> LandPlotWithOwners:
    """Получить участок по ID с владельцами (ФИО и доля) и финансовым субъектом."""
    plot = await get_plot_use_case.execute(
        plot_id=plot_id, cooperative_id=current_user.cooperative_id
    )

    if plot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Участок не найден",
        )

    if current_user.role != "admin" and current_user.cooperative_id != plot.cooperative_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к данному участку",
        )

    ownerships = await get_ownerships_use_case.execute(plot_id)
    owners_payload = []
    for o in ownerships:
        owner = await get_owner_use_case.execute(owner_id=o.owner_id)
        owner_name = owner.name if owner else "—"
        owners_payload.append(
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
                owner_name=owner_name,
            )
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
        owners=owners_payload,
        financial_subject_id=None,
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
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_create_land_plot_use_case),
) -> LandPlotWithOwners:
    """Создать участок с владельцами (treasurer, admin)."""
    # Override cooperative_id with user's cooperative for non-admin
    if current_user.role != "admin":
        plot_data.cooperative_id = current_user.cooperative_id

    plot, fs = await use_case.execute(data=plot_data, ownerships=plot_data.ownerships)

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
        financial_subject_id=fs.id,
        financial_subject_code=fs.code,
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
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_update_land_plot_use_case),
) -> LandPlotWithOwners:
    """Обновить участок (treasurer, admin)."""
    ownerships_in = getattr(plot_data, "ownerships", None)
    logger.info(
        "PATCH land-plots/%s: user=%s role=%s cooperative_id=%s, ownerships present=%s count=%s",
        plot_id,
        current_user.username,
        current_user.role,
        current_user.cooperative_id,
        ownerships_in is not None,
        len(ownerships_in) if ownerships_in else 0,
    )
    if ownerships_in:
        for idx, o in enumerate(ownerships_in):
            o_dict = (
                o.model_dump() if hasattr(o, "model_dump") else (o if isinstance(o, dict) else {})
            )
            logger.info(
                "PATCH land-plots/%s ownerships[%s]: %s",
                plot_id,
                idx,
                o_dict,
            )
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
    description="Удалить земельный участок. Казначей и председатель могут удалять участки в рамках своего товарищества, admin — в любом.",
)
async def delete_land_plot(
    plot_id: UUID,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_delete_land_plot_use_case),
) -> None:
    """Удалить участок."""
    # Admin can delete from any cooperative - pass None and let use case handle it
    deleted = await use_case.execute(plot_id=plot_id, cooperative_id=current_user.cooperative_id)

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
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_create_plot_ownership_use_case),
) -> PlotOwnershipInDB:
    """Добавить владельца к участку (treasurer, admin)."""
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
    valid_to: Annotated[str, Query(..., description="Дата прекращения владения")],
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_close_plot_ownership_use_case),
) -> PlotOwnershipInDB:
    """Закрыть право собственности (установить valid_to) (treasurer, admin)."""
    from datetime import date

    valid_to_date = date.fromisoformat(valid_to)

    ownership = await use_case.execute(
        ownership_id=ownership_id,
        valid_to=valid_to_date,
        cooperative_id=current_user.cooperative_id,
    )

    if ownership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Право собственности не найдено",
        )

    return ownership
