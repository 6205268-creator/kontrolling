"""FastAPI routes for financial_core module."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.models.app_user import AppUser

from .schemas import BalanceInfo, FinancialSubjectInfo
from app.modules.deps import (
    get_get_financial_subject_use_case,
    get_get_financial_subjects_use_case,
    get_get_balance_use_case,
    get_get_balances_by_cooperative_use_case,
)

router = APIRouter()


@router.get(
    "/",
    response_model=list[FinancialSubjectInfo],
    summary="Список финансовых субъектов",
    description="Получить список финансовых субъектов СТ. Admin видит все, chairman/treasurer — только своё СТ.",
)
async def get_financial_subjects(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_get_financial_subjects_use_case),
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

    subjects = await use_case.execute(cooperative_id=cooperative_id)

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
    get_subject_use_case=Depends(get_get_financial_subject_use_case),
    get_balance_use_case=Depends(get_get_balance_use_case),
) -> BalanceInfo:
    """Получить баланс конкретного финансового субъекта."""
    # Check access
    subject = await get_subject_use_case.execute(
        subject_id=subject_id,
        cooperative_id=current_user.cooperative_id,
    )

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

    balance = await get_balance_use_case.execute(financial_subject_id=subject_id)

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
    use_case=Depends(get_get_balances_by_cooperative_use_case),
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

    balances = await use_case.execute(cooperative_id=cooperative_id)

    return [
        BalanceInfo(
            financial_subject_id=b.financial_subject_id,
            subject_type=b.subject_type,
            subject_id=b.subject_id,
            cooperative_id=b.cooperative_id,
            code=b.code,
            total_accruals=b.total_accruals,
            total_payments=b.total_payments,
            balance=b.balance,
        )
        for b in balances
    ]
