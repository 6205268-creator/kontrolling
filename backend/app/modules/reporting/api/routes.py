"""FastAPI routes for reporting module."""

from datetime import date
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.modules.administration.domain.entities import AppUser
from app.modules.deps import (
    get_generate_cash_flow_use_case,
    get_generate_debtor_report_use_case,
    get_turnover_sheet_use_case,
)

from .schemas import CashFlowReport, DebtorInfo, TurnoverSheetRowOut

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
    as_of_date: date | None = Query(None, description="Дата отчёта (по умолчанию — сегодня)"),
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

    ref_date = as_of_date or date.today()
    debtors = await use_case.execute(
        cooperative_id=cooperative_id,
        as_of_date=ref_date,
        min_debt=min_debt,
    )

    return [
        DebtorInfo(
            financial_subject_id=UUID(d.financial_subject_id),
            subject_type=d.subject_type,
            subject_info=d.subject_info,
            owner_name=d.owner_name,
            total_debt=d.total_debt,
            overdue_days=d.overdue_days,
            penalty_amount=d.penalty_amount,
            total_with_penalty=d.total_with_penalty,
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


@router.get(
    "/turnover",
    response_model=list[TurnoverSheetRowOut],
    summary="Оборотная ведомость",
    description="Сальдо на начало, начисления, платежи и сальдо на конец за месяц.",
)
async def get_turnover_sheet(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_turnover_sheet_use_case),
    cooperative_id: UUID | None = Query(None, description="ID СТ"),
    year: int = Query(..., ge=2000, le=2100, description="Год"),
    month: int = Query(..., ge=1, le=12, description="Месяц (1–12)"),
) -> list[TurnoverSheetRowOut]:
    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id

    if cooperative_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать cooperative_id",
        )

    rows = await use_case.execute(cooperative_id=cooperative_id, year=year, month=month)
    return [
        TurnoverSheetRowOut(
            financial_subject_id=r.financial_subject_id,
            code=r.code,
            opening_balance=r.opening_balance,
            accrued_in_period=r.accrued_in_period,
            paid_in_period=r.paid_in_period,
            closing_balance=r.closing_balance,
        )
        for r in rows
    ]
