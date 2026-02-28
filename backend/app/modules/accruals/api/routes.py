"""FastAPI routes for accruals module."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.app_user import AppUser

from .schemas import AccrualBatchCreate, AccrualCreate, AccrualInDB
from ..infrastructure.repositories import AccrualRepository
from ..application.use_cases import (
    CreateAccrualUseCase,
    GetAccrualUseCase,
    GetAccrualsByFinancialSubjectUseCase,
    GetAccrualsByCooperativeUseCase,
    ApplyAccrualUseCase,
    CancelAccrualUseCase,
    MassCreateAccrualsUseCase,
)

router = APIRouter()


def _get_accrual_repo(db: AsyncSession) -> AccrualRepository:
    """Get accrual repository instance."""
    return AccrualRepository(db)


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

    repo = _get_accrual_repo(db)
    
    if financial_subject_id:
        use_case = GetAccrualsByFinancialSubjectUseCase(repo)
        accruals = await use_case.execute(
            financial_subject_id=financial_subject_id,
            cooperative_id=cooperative_id,  # type: ignore[arg-type]
        )
    elif cooperative_id:
        use_case = GetAccrualsByCooperativeUseCase(repo)
        accruals = await use_case.execute(cooperative_id=cooperative_id)
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
    db: AsyncSession = Depends(get_db),
) -> AccrualInDB:
    """Создать начисление (treasurer, admin)."""
    # Check access to financial subject
    from app.modules.financial_core.infrastructure.repositories import FinancialSubjectRepository
    
    fs_repo = FinancialSubjectRepository(db)
    subject = await fs_repo.get_by_id(accrual_data.financial_subject_id, current_user.cooperative_id)
    
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Финансовый субъект не найден",
        )

    # Check access: admin sees all, others only their cooperative
    if current_user.role != "admin" and current_user.cooperative_id != subject.cooperative_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к данному финансовому субъекту",
        )

    repo = _get_accrual_repo(db)
    use_case = CreateAccrualUseCase(repo)
    
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
    db: AsyncSession = Depends(get_db),
) -> list[AccrualInDB]:
    """Массовое создание начислений (treasurer, admin)."""
    from app.modules.financial_core.infrastructure.repositories import FinancialSubjectRepository
    
    fs_repo = FinancialSubjectRepository(db)
    
    # Check access to all financial subjects
    subject_ids = {a.financial_subject_id for a in batch_data.accruals}
    for subject_id in subject_ids:
        subject = await fs_repo.get_by_id(subject_id, current_user.cooperative_id)
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

    repo = _get_accrual_repo(db)
    use_case = MassCreateAccrualsUseCase(repo)
    
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
    db: AsyncSession = Depends(get_db),
) -> AccrualInDB:
    """Применить начисление (смена статуса на "applied") (treasurer, admin)."""
    repo = _get_accrual_repo(db)
    use_case = ApplyAccrualUseCase(repo)
    
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
    db: AsyncSession = Depends(get_db),
) -> AccrualInDB:
    """Отменить начисление (смена статуса на "cancelled") (treasurer, admin)."""
    repo = _get_accrual_repo(db)
    use_case = CancelAccrualUseCase(repo)
    
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
