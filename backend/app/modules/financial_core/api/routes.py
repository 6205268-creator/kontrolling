"""FastAPI routes for financial_core module."""

from datetime import UTC, date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.modules.administration.domain.entities import AppUser
from app.modules.deps import (
    get_close_financial_period_use_case,
    get_cooperative_repository,
    get_create_financial_period_use_case,
    get_financial_period_by_date_use_case,
    get_financial_periods_use_case,
    get_get_balance_use_case,
    get_get_balances_by_cooperative_use_case,
    get_get_financial_subject_use_case,
    get_get_financial_subjects_use_case,
    get_lock_financial_period_use_case,
    get_reopen_financial_period_use_case,
)

from .schemas import (
    BalanceInfo,
    FinancialPeriodClose,
    FinancialPeriodCreate,
    FinancialPeriodInDB,
    FinancialPeriodReopen,
    FinancialSubjectInfo,
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
    as_of_date: date | None = Query(None, description="Баланс на дату (по умолчанию — текущая)"),
    cooperative_id: UUID | None = Query(None, description="ID СТ (для admin)"),
) -> BalanceInfo:
    """Получить баланс конкретного финансового субъекта."""
    # Check access
    # Для admin используем cooperative_id из query, для остальных — из пользователя
    user_cooperative_id = (
        current_user.cooperative_id if current_user.role != "admin" else cooperative_id
    )

    if current_user.role == "admin" and user_cooperative_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin должен указать cooperative_id в query параметрах",
        )

    subject = await get_subject_use_case.execute(
        subject_id=subject_id,
        cooperative_id=user_cooperative_id,
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

    balance = await get_balance_use_case.execute(
        financial_subject_id=subject_id, as_of_date=as_of_date
    )

    if balance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Финансовый субъект не найден",
        )

    return BalanceInfo(
        financial_subject_id=balance.financial_subject_id,
        subject_type=balance.subject_type,
        subject_id=balance.subject_id,
        cooperative_id=balance.cooperative_id,
        code=balance.code,
        total_accruals=balance.total_accruals.to_decimal(),
        total_payments=balance.total_payments.to_decimal(),
        balance=balance.balance.to_decimal(),
    )


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
    as_of_date: date | None = Query(None, description="Балансы на дату (по умолчанию — текущая)"),
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

    balances = await use_case.execute(cooperative_id=cooperative_id, as_of_date=as_of_date)

    return [
        BalanceInfo(
            financial_subject_id=b.financial_subject_id,
            subject_type=b.subject_type,
            subject_id=b.subject_id,
            cooperative_id=b.cooperative_id,
            code=b.code,
            total_accruals=b.total_accruals.to_decimal(),
            total_payments=b.total_payments.to_decimal(),
            balance=b.balance.to_decimal(),
        )
        for b in balances
    ]


# =============================================================================
# Financial Period Routes
# =============================================================================


@router.get(
    "/periods",
    response_model=list[FinancialPeriodInDB],
    summary="Список финансовых периодов",
    description="Получить список финансовых периодов СТ.",
)
async def get_financial_periods(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_financial_periods_use_case),
    cooperative_id: UUID | None = Query(None, description="ID СТ"),
    year: int | None = Query(None, ge=1900, le=2100, description="Год"),
) -> list[FinancialPeriodInDB]:
    """Get financial periods for cooperative."""
    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id
    elif cooperative_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cooperative_id is required for admin users",
        )

    periods = await use_case.execute(cooperative_id=cooperative_id, year=year)

    return [
        FinancialPeriodInDB(
            id=p.id,
            cooperative_id=p.cooperative_id,
            period_type=p.period_type.value,
            year=p.year,
            month=p.month,
            start_date=p.start_date,
            end_date=p.end_date,
            status=p.status,
            closed_at=p.closed_at,
            closed_by_user_id=p.closed_by_user_id,
            created_at=p.created_at,
        )
        for p in periods
    ]


@router.get(
    "/periods/by-date",
    response_model=FinancialPeriodInDB | None,
    summary="Период по дате",
    description="Найти финансовый период, содержащий указанную дату.",
)
async def get_period_by_date(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_financial_period_by_date_use_case),
    date: date = Query(..., description="Дата для поиска периода"),
    cooperative_id: UUID | None = Query(None, description="ID СТ"),
) -> FinancialPeriodInDB | None:
    """Get financial period containing the given date."""
    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id
    elif cooperative_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cooperative_id is required for admin users",
        )

    period = await use_case.execute(cooperative_id=cooperative_id, date=date)

    if not period:
        return None

    return FinancialPeriodInDB(
        id=period.id,
        cooperative_id=period.cooperative_id,
        period_type=period.period_type.value,
        year=period.year,
        month=period.month,
        start_date=period.start_date,
        end_date=period.end_date,
        status=period.status,
        closed_at=period.closed_at,
        closed_by_user_id=period.closed_by_user_id,
        created_at=period.created_at,
    )


@router.post(
    "/periods",
    response_model=FinancialPeriodInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Создать финансовый период",
    description="Создать новый финансовый период (месячный или годовой).",
)
async def create_financial_period(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    data: FinancialPeriodCreate,
    use_case=Depends(get_create_financial_period_use_case),
    cooperative_id: UUID | None = Query(None, description="ID СТ"),
) -> FinancialPeriodInDB:
    """Create a new financial period."""
    if current_user.role not in ("admin", "chairman"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or chairman can create periods",
        )

    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id
    elif cooperative_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cooperative_id is required for admin users",
        )

    period = await use_case.execute(
        cooperative_id=cooperative_id,
        period_type=data.period_type,
        year=data.year,
        month=data.month,
    )

    return FinancialPeriodInDB(
        id=period.id,
        cooperative_id=period.cooperative_id,
        period_type=period.period_type.value,
        year=period.year,
        month=period.month,
        start_date=period.start_date,
        end_date=period.end_date,
        status=period.status,
        closed_at=period.closed_at,
        closed_by_user_id=period.closed_by_user_id,
        created_at=period.created_at,
    )


@router.post(
    "/periods/{period_id}/close",
    response_model=FinancialPeriodInDB,
    summary="Закрыть финансовый период",
    description="Закрыть финансовый период (переводит в статус closed).",
)
async def close_financial_period(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    period_id: UUID,
    data: FinancialPeriodClose,
    use_case=Depends(get_close_financial_period_use_case),
    cooperative_id: UUID | None = Query(None, description="ID СТ"),
) -> FinancialPeriodInDB:
    """Close a financial period."""
    if current_user.role not in ("admin", "chairman", "treasurer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin, chairman or treasurer can close periods",
        )

    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id
    elif cooperative_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cooperative_id is required for admin users",
        )

    try:
        period = await use_case.execute(
            period_id=period_id,
            cooperative_id=cooperative_id,
            user_id=current_user.id,
            now=datetime.now(UTC),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    return FinancialPeriodInDB(
        id=period.id,
        cooperative_id=period.cooperative_id,
        period_type=period.period_type.value,
        year=period.year,
        month=period.month,
        start_date=period.start_date,
        end_date=period.end_date,
        status=period.status,
        closed_at=period.closed_at,
        closed_by_user_id=period.closed_by_user_id,
        created_at=period.created_at,
    )


@router.post(
    "/periods/{period_id}/reopen",
    response_model=FinancialPeriodInDB,
    summary="Переоткрыть финансовый период",
    description="Переоткрыть закрытый период (казначей — в пределах N дней, admin — всегда).",
)
async def reopen_financial_period(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    period_id: UUID,
    data: FinancialPeriodReopen,
    use_case=Depends(get_reopen_financial_period_use_case),
    coop_repo=Depends(get_cooperative_repository),
    cooperative_id: UUID | None = Query(None, description="ID СТ"),
) -> FinancialPeriodInDB:
    """Reopen a financial period."""
    if current_user.role not in ("admin", "treasurer", "chairman"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin, chairman or treasurer can reopen periods",
        )

    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id
    elif cooperative_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cooperative_id is required for admin users",
        )

    coop = await coop_repo.get_by_id(
        cooperative_id,
        None if current_user.role == "admin" else current_user.cooperative_id,
    )
    period_reopen_allowed_days = coop.period_reopen_allowed_days if coop else 30

    try:
        period = await use_case.execute(
            period_id=period_id,
            cooperative_id=cooperative_id,
            user_id=current_user.id,
            now=datetime.now(UTC),
            is_admin=current_user.role == "admin",
            period_reopen_allowed_days=period_reopen_allowed_days,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    return FinancialPeriodInDB(
        id=period.id,
        cooperative_id=period.cooperative_id,
        period_type=period.period_type.value,
        year=period.year,
        month=period.month,
        start_date=period.start_date,
        end_date=period.end_date,
        status=period.status,
        closed_at=period.closed_at,
        closed_by_user_id=period.closed_by_user_id,
        created_at=period.created_at,
    )


@router.post(
    "/periods/{period_id}/lock",
    response_model=FinancialPeriodInDB,
    summary="Заблокировать финансовый период",
    description="Заблокировать период (только admin).",
)
async def lock_financial_period(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    period_id: UUID,
    use_case=Depends(get_lock_financial_period_use_case),
    cooperative_id: UUID | None = Query(None, description="ID СТ"),
) -> FinancialPeriodInDB:
    """Lock a financial period (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can lock periods",
        )

    if cooperative_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cooperative_id is required",
        )

    try:
        period = await use_case.execute(
            period_id=period_id,
            cooperative_id=cooperative_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    return FinancialPeriodInDB(
        id=period.id,
        cooperative_id=period.cooperative_id,
        period_type=period.period_type.value,
        year=period.year,
        month=period.month,
        start_date=period.start_date,
        end_date=period.end_date,
        status=period.status,
        closed_at=period.closed_at,
        closed_by_user_id=period.closed_by_user_id,
        created_at=period.created_at,
    )
