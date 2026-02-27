from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.app_user import AppUser
from app.schemas.report import CashFlowReport, DebtorInfo
from app.services import report_service

router = APIRouter()


@router.get(
    "/debtors",
    response_model=list[DebtorInfo],
    summary="Отчёт по должникам",
    description="Получить список финансовых субъектов с задолженностью больше указанной суммы.",
)
async def get_debtors_report(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    cooperative_id: str | None = Query(None, description="ID СТ для отчёта"),
    min_debt: Decimal = Query(Decimal("0.00"), description="Минимальная сумма задолженности"),
) -> list[DebtorInfo]:
    """
    Отчёт по должникам СТ.

    Возвращает список финансовых субъектов с задолженностью > min_debt.

    Доступ:
    - **admin**: может указать любой cooperative_id
    - **chairman/treasurer**: видят только отчёты своего СТ
    """
    # Для не-admin пользователей используем их СТ
    if current_user.role != "admin":
        cooperative_id = str(current_user.cooperative_id) if current_user.cooperative_id else None

    if cooperative_id is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать cooperative_id",
        )

    try:
        from uuid import UUID

        coop_uuid = UUID(cooperative_id)
    except ValueError:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный формат cooperative_id",
        )

    debtors = await report_service.get_debtors_report(db, coop_uuid, min_debt)
    return debtors


@router.get(
    "/cash-flow",
    response_model=CashFlowReport,
    summary="Отчёт о движении денежных средств",
    description="Получить отчёт о начислениях, платежах и расходах за указанный период.",
)
async def get_cash_flow_report(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    cooperative_id: str | None = Query(None, description="ID СТ для отчёта"),
    period_start: date = Query(..., description="Начало отчётного периода"),
    period_end: date = Query(..., description="Конец отчётного периода"),
) -> CashFlowReport:
    """
    Отчёт о движении денежных средств за период.

    Возвращает суммы начислений, платежей и расходов за указанный период.

    Доступ:
    - **admin**: может указать любой cooperative_id
    - **chairman/treasurer**: видят только отчёты своего СТ
    """
    # Для не-admin пользователей используем их СТ
    if current_user.role != "admin":
        cooperative_id = str(current_user.cooperative_id) if current_user.cooperative_id else None

    if cooperative_id is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать cooperative_id",
        )

    try:
        from uuid import UUID

        coop_uuid = UUID(cooperative_id)
    except ValueError:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный формат cooperative_id",
        )

    report = await report_service.get_cash_flow_report(db, coop_uuid, period_start, period_end)
    return report
