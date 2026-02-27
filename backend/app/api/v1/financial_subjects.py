from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.app_user import AppUser
from app.schemas.balance import BalanceInfo, FinancialSubjectInfo
from app.services import balance_service

router = APIRouter()


@router.get(
    "/",
    response_model=list[FinancialSubjectInfo],
    summary="Список финансовых субъектов",
    description="Получить список финансовых субъектов СТ. Admin видит все, chairman/treasurer — только своё СТ.",
)
async def get_financial_subjects(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    cooperative_id: UUID | None = Query(None, description="Фильтр по СТ"),
) -> list[FinancialSubjectInfo]:
    """
    Получить список финансовых субъектов.

    - **admin**: может указать cooperative_id или получить все
    - **chairman/treasurer**: видят только субъекты своего СТ
    """
    # Для не-admin пользователей используем их СТ
    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id

    if cooperative_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать cooperative_id",
        )

    subjects = await balance_service.get_financial_subjects_by_cooperative(db, cooperative_id)
    return [
        FinancialSubjectInfo(
            id=s.id,
            subject_type=s.subject_type,
            subject_id=s.subject_id,
            cooperative_id=s.cooperative_id,
            code=s.code,
            status=s.status,
        )
        for s in subjects
    ]


@router.get(
    "/{subject_id}/balance",
    response_model=BalanceInfo,
    summary="Баланс финансового субъекта",
    description="Получить баланс конкретного финансового субъекта (разница между начислениями и платежами).",
)
async def get_financial_subject_balance(
    subject_id: UUID,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> BalanceInfo:
    """Получить баланс конкретного финансового субъекта."""
    # Проверяем доступ
    subject = await balance_service.get_financial_subject(db, subject_id)
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

    balance = await balance_service.calculate_balance(db, subject_id)
    if balance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Финансовый субъект не найден",
        )

    return balance


@router.get(
    "/balances",
    response_model=list[BalanceInfo],
    summary="Балансы всех субъектов СТ",
    description="Получить балансы всех финансовых субъектов садоводческого товарищества.",
)
async def get_balances_by_cooperative(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    cooperative_id: UUID | None = Query(None, description="ID СТ"),
) -> list[BalanceInfo]:
    """
    Получить балансы всех финансовых субъектов СТ.

    - **admin**: может указать любой cooperative_id
    - **chairman/treasurer**: видят только балансы своего СТ
    """
    # Для не-admin пользователей используем их СТ
    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id

    if cooperative_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать cooperative_id",
        )

    balances = await balance_service.get_balances_by_cooperative(db, cooperative_id)
    return balances
