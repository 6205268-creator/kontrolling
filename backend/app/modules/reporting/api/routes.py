"""FastAPI routes for reporting module."""

from datetime import date
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.modules.administration.domain.entities import AppUser
from app.modules.deps import (
    get_generate_debtor_report_use_case,
    get_generate_cash_flow_use_case,
)

from .schemas import CashFlowReport, DebtorInfo

router = APIRouter()


@router.get(
    "/debtors",
    response_model=list[DebtorInfo],
    summary="Отчёт по должникам",
    description="Получить список финансовых субъектов с задолженностью.",
)
async def get_debtors_report(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_generate_debtor_report_use_case),
    cooperative_id: UUID | None = Query(None, description="ID СТ для отчёта"),
    min_debt: Decimal = Query(Decimal("0.00"), description="Минимальная сумма задолженности"),
) -> list[DebtorInfo]:
    """Get debtors report."""
    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id

    if cooperative_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать cooperative_id",
        )

    debtors = await use_case.execute(cooperative_id=cooperative_id, min_debt=min_debt)
    
    return [
        DebtorInfo(
            financial_subject_id=UUID(d.financial_subject_id),
            subject_type=d.subject_type,
            subject_info=d.subject_info,
            owner_name=d.owner_name,
            total_debt=d.total_debt,
        )
        for d in debtors
    ]


@router.get(
    "/cash-flow",
    response_model=CashFlowReport,
    summary="Отчёт о движении денежных средств",
    description="Получить отчёт о начислениях, платежах и расходах за период.",
)
async def get_cash_flow_report(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_generate_cash_flow_use_case),
    cooperative_id: UUID | None = Query(None, description="ID СТ для отчёта"),
    period_start: date = Query(..., description="Начало отчётного периода"),
    period_end: date = Query(..., description="Конец отчётного периода"),
) -> CashFlowReport:
    """Get cash flow report."""
    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id

    if cooperative_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать cooperative_id",
        )

    report = await use_case.execute(
        cooperative_id=cooperative_id,
        period_start=period_start,
        period_end=period_end,
    )
    return CashFlowReport(
        period_start=report.period_start,
        period_end=report.period_end,
        total_accruals=report.total_accruals,
        total_payments=report.total_payments,
        total_expenses=report.total_expenses,
        net_balance=report.net_balance,
    )
