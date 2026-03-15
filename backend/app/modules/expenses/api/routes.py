"""FastAPI routes for expenses module."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.modules.administration.domain.entities import AppUser
from app.modules.deps import (
    get_cancel_expense_use_case,
    get_confirm_expense_use_case,
    get_create_expense_use_case,
    get_expense_categories_use_case,
    get_expenses_by_cooperative_use_case,
)
from app.modules.shared.kernel.exceptions import DomainError, ValidationError

from .schemas import ExpenseCategoryInDB, ExpenseCreate, ExpenseInDB

router = APIRouter()


class CancelBody(BaseModel):
    """Request body for cancel endpoint."""

    reason: str | None = Field(None, description="Причина отмены", max_length=512)


@router.get(
    "/categories",
    response_model=list[ExpenseCategoryInDB],
    summary="Категории расходов",
    description="Получить справочник категорий расходов.",
)
async def get_expense_categories(
    use_case=Depends(get_expense_categories_use_case),
) -> list[ExpenseCategoryInDB]:
    """Get expense categories."""
    categories = await use_case.execute()

    return [
        ExpenseCategoryInDB(
            id=c.id,
            name=c.name,
            code=c.code,
            description=c.description,
            created_at=c.created_at,
        )
        for c in categories
    ]


@router.get(
    "/",
    response_model=list[ExpenseInDB],
    summary="Список расходов",
    description="Получить список расходов садоводческого товарищества.",
)
async def get_expenses(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_expenses_by_cooperative_use_case),
    cooperative_id: UUID | None = Query(None, description="Фильтр по СТ"),
) -> list[ExpenseInDB]:
    """Get expenses by cooperative."""
    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id

    if cooperative_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать cooperative_id",
        )

    expenses = await use_case.execute(cooperative_id=cooperative_id)

    return [
        ExpenseInDB(
            id=e.id,
            cooperative_id=e.cooperative_id,
            category_id=e.category_id,
            amount=e.amount,
            expense_date=e.expense_date,
            document_number=e.document_number,
            description=e.description,
            status=e.status,
            created_at=e.created_at,
            updated_at=e.updated_at,
            cancelled_at=e.cancelled_at,
            cancelled_by_user_id=e.cancelled_by_user_id,
            cancellation_reason=e.cancellation_reason,
            operation_number=e.operation_number,
        )
        for e in expenses
    ]


@router.post(
    "/",
    response_model=ExpenseInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Создать расход",
    description="Создать новый расход товарищества. Доступно: treasurer, admin.",
)
async def create_expense(
    expense_data: ExpenseCreate,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_create_expense_use_case),
) -> ExpenseInDB:
    """Create an expense."""
    if current_user.role != "admin" and current_user.cooperative_id != expense_data.cooperative_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к данному СТ",
        )

    try:
        expense = await use_case.execute(
            data=expense_data, cooperative_id=current_user.cooperative_id
        )
    except ValidationError as e:
        if "category" in str(e).lower() or "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ExpenseInDB(
        id=expense.id,
        cooperative_id=expense.cooperative_id,
        category_id=expense.category_id,
        amount=expense.amount,
        expense_date=expense.expense_date,
        document_number=expense.document_number,
        description=expense.description,
        status=expense.status,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
        cancelled_at=expense.cancelled_at,
        cancelled_by_user_id=expense.cancelled_by_user_id,
        cancellation_reason=expense.cancellation_reason,
        operation_number=expense.operation_number,
    )


@router.post(
    "/{expense_id}/confirm",
    response_model=ExpenseInDB,
    summary="Подтвердить расход",
    description="Изменить статус расхода на 'confirmed'. Доступно: treasurer, admin.",
)
async def confirm_expense(
    expense_id: UUID,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_confirm_expense_use_case),
) -> ExpenseInDB:
    """Confirm expense."""
    try:
        expense = await use_case.execute(
            expense_id=expense_id, cooperative_id=current_user.cooperative_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ExpenseInDB(
        id=expense.id,
        cooperative_id=expense.cooperative_id,
        category_id=expense.category_id,
        amount=expense.amount,
        expense_date=expense.expense_date,
        document_number=expense.document_number,
        description=expense.description,
        status=expense.status,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
        cancelled_at=expense.cancelled_at,
        cancelled_by_user_id=expense.cancelled_by_user_id,
        cancellation_reason=expense.cancellation_reason,
        operation_number=expense.operation_number,
    )


@router.post(
    "/{expense_id}/cancel",
    response_model=ExpenseInDB,
    summary="Отменить расход",
    description="Изменить статус расхода на 'cancelled'. Доступно: treasurer, admin.",
)
async def cancel_expense(
    expense_id: UUID,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_cancel_expense_use_case),
    body: CancelBody | None = None,
) -> ExpenseInDB:
    """Cancel expense."""
    try:
        expense = await use_case.execute(
            expense_id=expense_id,
            cooperative_id=current_user.cooperative_id,
            cancelled_by_user_id=current_user.id,
            cancellation_reason=body.reason if body else None,
        )
    except DomainError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ExpenseInDB(
        id=expense.id,
        cooperative_id=expense.cooperative_id,
        category_id=expense.category_id,
        amount=expense.amount,
        expense_date=expense.expense_date,
        document_number=expense.document_number,
        description=expense.description,
        status=expense.status,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
        cancelled_at=expense.cancelled_at,
        cancelled_by_user_id=expense.cancelled_by_user_id,
        cancellation_reason=expense.cancellation_reason,
        operation_number=expense.operation_number,
    )
