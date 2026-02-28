"""FastAPI routes for accruals module."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user, require_role
from app.models.app_user import AppUser

from .schemas import AccrualBatchCreate, AccrualCreate, AccrualInDB
from app.modules.deps import (
    get_create_accrual_use_case,
    get_get_accrual_use_case,
    get_accruals_by_financial_subject_use_case,
    get_accruals_by_cooperative_use_case,
    get_apply_accrual_use_case,
    get_cancel_accrual_use_case,
    get_mass_create_accruals_use_case,
)

router = APIRouter()


@router.get(
    "/",
    response_model=list[AccrualInDB],
    summary="Список начислений",
    description="Получить список начислений по финансовому субъекту или СТ.",
)
async def get_accruals(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    fs_use_case=Depends(get_accruals_by_financial_subject_use_case),
    coop_use_case=Depends(get_accruals_by_cooperative_use_case),
    financial_subject_id: UUID | None = Query(None, description="Фильтр по финансовому субъекту"),
    cooperative_id: UUID | None = Query(None, description="Фильтр по СТ"),
) -> list[AccrualInDB]:
    """
    Получить список начислений.

    - **admin**: может фильтровать по любому cooperative_id
    - **chairman/treasurer**: видят только начисления своего СТ
    """
    # Для не-admin пользователей используем их СТ
    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id

    if financial_subject_id:
        accruals = await fs_use_case.execute(
            financial_subject_id=financial_subject_id,
            cooperative_id=cooperative_id,  # type: ignore[arg-type]
        )
    elif cooperative_id:
        accruals = await coop_use_case.execute(cooperative_id=cooperative_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать financial_subject_id или cooperative_id",
        )

    return [
        AccrualInDB(
            id=a.id,
            financial_subject_id=a.financial_subject_id,
            contribution_type_id=a.contribution_type_id,
            amount=a.amount,
            accrual_date=a.accrual_date,
            period_start=a.period_start,
            period_end=a.period_end,
            status=a.status,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in accruals
    ]


@router.post(
    "/",
    response_model=AccrualInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Создать начисление",
    description="Создать новое начисление для финансового субъекта. Доступно: treasurer, admin.",
)
async def create_accrual(
    accrual_data: AccrualCreate,
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    use_case=Depends(get_create_accrual_use_case),
) -> AccrualInDB:
    """Создать начисление (treasurer, admin)."""
    accrual = await use_case.execute(data=accrual_data, cooperative_id=current_user.cooperative_id)

    return AccrualInDB(
        id=accrual.id,
        financial_subject_id=accrual.financial_subject_id,
        contribution_type_id=accrual.contribution_type_id,
        amount=accrual.amount,
        accrual_date=accrual.accrual_date,
        period_start=accrual.period_start,
        period_end=accrual.period_end,
        status=accrual.status,
        created_at=accrual.created_at,
        updated_at=accrual.updated_at,
    )


@router.post(
    "/batch",
    response_model=list[AccrualInDB],
    status_code=status.HTTP_201_CREATED,
    summary="Массовое создание начислений",
    description="Создать несколько начислений одновременно. Доступно: treasurer, admin.",
)
async def mass_create_accruals(
    batch_data: AccrualBatchCreate,
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    use_case=Depends(get_mass_create_accruals_use_case),
) -> list[AccrualInDB]:
    """Массовое создание начислений (treasurer, admin)."""
    accruals = await use_case.execute(
        accruals_data=batch_data.accruals,
        cooperative_id=current_user.cooperative_id,
    )

    return [
        AccrualInDB(
            id=a.id,
            financial_subject_id=a.financial_subject_id,
            contribution_type_id=a.contribution_type_id,
            amount=a.amount,
            accrual_date=a.accrual_date,
            period_start=a.period_start,
            period_end=a.period_end,
            status=a.status,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in accruals
    ]


@router.post(
    "/{accrual_id}/apply",
    response_model=AccrualInDB,
    summary="Применить начисление",
    description="Изменить статус начисления на 'applied'. Доступно: treasurer, admin.",
)
async def apply_accrual(
    accrual_id: UUID,
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    use_case=Depends(get_apply_accrual_use_case),
) -> AccrualInDB:
    """Применить начисление (смена статуса на "applied") (treasurer, admin)."""
    try:
        accrual = await use_case.execute(
            accrual_id=accrual_id,
            cooperative_id=current_user.cooperative_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return AccrualInDB(
        id=accrual.id,
        financial_subject_id=accrual.financial_subject_id,
        contribution_type_id=accrual.contribution_type_id,
        amount=accrual.amount,
        accrual_date=accrual.accrual_date,
        period_start=accrual.period_start,
        period_end=accrual.period_end,
        status=accrual.status,
        created_at=accrual.created_at,
        updated_at=accrual.updated_at,
    )


@router.post(
    "/{accrual_id}/cancel",
    response_model=AccrualInDB,
    summary="Отменить начисление",
    description="Изменить статус начисления на 'cancelled'. Доступно: treasurer, admin.",
)
async def cancel_accrual(
    accrual_id: UUID,
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    use_case=Depends(get_cancel_accrual_use_case),
) -> AccrualInDB:
    """Отменить начисление (смена статуса на "cancelled") (treasurer, admin)."""
    try:
        accrual = await use_case.execute(
            accrual_id=accrual_id,
            cooperative_id=current_user.cooperative_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return AccrualInDB(
        id=accrual.id,
        financial_subject_id=accrual.financial_subject_id,
        contribution_type_id=accrual.contribution_type_id,
        amount=accrual.amount,
        accrual_date=accrual.accrual_date,
        period_start=accrual.period_start,
        period_end=accrual.period_end,
        status=accrual.status,
        created_at=accrual.created_at,
        updated_at=accrual.updated_at,
    )
