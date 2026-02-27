from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.app_user import AppUser
from app.schemas.accrual import AccrualCreate, AccrualInDB, AccrualBatchCreate
from app.services import accrual_service

router = APIRouter()


@router.get(
    "/",
    response_model=list[AccrualInDB],
    summary="Список начислений",
    description="Получить список начислений по финансовому субъекту или СТ.",
)
async def get_accruals(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
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
        accruals = await accrual_service.get_accruals_by_financial_subject(db, financial_subject_id)
    elif cooperative_id:
        accruals = await accrual_service.get_accruals_by_cooperative(db, cooperative_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать financial_subject_id или cooperative_id",
        )

    return accruals


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
    db: AsyncSession = Depends(get_db),
) -> AccrualInDB:
    """Создать начисление (treasurer, admin)."""
    # Проверка доступа к финансовому субъекту
    from app.services.balance_service import get_financial_subject

    subject = await get_financial_subject(db, accrual_data.financial_subject_id)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Финансовый субъект не найден",
        )

    # Проверка доступа: admin видит все, остальные только своё СТ
    if current_user.role != "admin" and current_user.cooperative_id != subject.cooperative_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к данному финансовому субъекту",
        )

    accrual = await accrual_service.create_accrual(db, accrual_data)
    return accrual


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
    db: AsyncSession = Depends(get_db),
) -> list[AccrualInDB]:
    """Массовое создание начислений (treasurer, admin)."""
    from app.services.balance_service import get_financial_subject

    # Проверка доступа ко всем финансовым субъектам
    subject_ids = {a.financial_subject_id for a in batch_data.accruals}
    for subject_id in subject_ids:
        subject = await get_financial_subject(db, subject_id)
        if subject is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Финансовый субъект {subject_id} не найден",
            )

        if current_user.role != "admin" and current_user.cooperative_id != subject.cooperative_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Нет доступа к финансовому субъекту {subject_id}",
            )

    accruals = await accrual_service.mass_create_accruals(db, batch_data.accruals)
    return accruals


@router.post(
    "/{accrual_id}/apply",
    response_model=AccrualInDB,
    summary="Применить начисление",
    description="Изменить статус начисления на 'applied'. Доступно: treasurer, admin.",
)
async def apply_accrual(
    accrual_id: UUID,
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    db: AsyncSession = Depends(get_db),
) -> AccrualInDB:
    """Применить начисление (смена статуса на "applied") (treasurer, admin)."""
    accrual = await accrual_service.apply_accrual(db, accrual_id)
    return accrual


@router.post(
    "/{accrual_id}/cancel",
    response_model=AccrualInDB,
    summary="Отменить начисление",
    description="Изменить статус начисления на 'cancelled'. Доступно: treasurer, admin.",
)
async def cancel_accrual(
    accrual_id: UUID,
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    db: AsyncSession = Depends(get_db),
) -> AccrualInDB:
    """Отменить начисление (смена статуса на "cancelled") (treasurer, admin)."""
    accrual = await accrual_service.cancel_accrual(db, accrual_id)
    return accrual
