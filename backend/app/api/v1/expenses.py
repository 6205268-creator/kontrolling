from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.app_user import AppUser
from app.schemas.expense import ExpenseCategoryInDB, ExpenseCreate, ExpenseInDB
from app.services import expense_service

router = APIRouter()


@router.get(
    "/categories",
    response_model=list[ExpenseCategoryInDB],
    summary="Категории расходов",
    description="Получить справочник категорий расходов (Дороги, Зарплата и т.д.).",
)
async def get_expense_categories(
    db: AsyncSession = Depends(get_db),
) -> list[ExpenseCategoryInDB]:
    """Получить список категорий расходов."""
    categories = await expense_service.get_expense_categories(db)
    return categories


@router.get(
    "/",
    response_model=list[ExpenseInDB],
    summary="Список расходов",
    description="Получить список расходов садоводческого товарищества.",
)
async def get_expenses(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    cooperative_id: UUID | None = Query(None, description="Фильтр по СТ"),
) -> list[ExpenseInDB]:
    """
    Получить список расходов.

    - **admin**: может указать любой cooperative_id
    - **chairman/treasurer**: видят только расходы своего СТ
    """
    # Для не-admin пользователей используем их СТ
    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id

    if cooperative_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать cooperative_id",
        )

    expenses = await expense_service.get_expenses_by_cooperative(db, cooperative_id)
    return expenses


@router.post(
    "/",
    response_model=ExpenseInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Создать расход",
    description="Создать новый расход товарищества. Доступно: treasurer, admin.",
)
async def create_expense(
    expense_data: ExpenseCreate,
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    db: AsyncSession = Depends(get_db),
) -> ExpenseInDB:
    """Создать расход (treasurer, admin)."""
    # Проверка доступа: admin видит все, остальные только своё СТ
    if current_user.role != "admin" and current_user.cooperative_id != expense_data.cooperative_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к данному СТ",
        )

    # Проверка существования категории
    category = await expense_service.get_expense_category(db, expense_data.category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория расхода не найдена",
        )

    expense = await expense_service.create_expense(db, expense_data)
    return expense


@router.post(
    "/{expense_id}/confirm",
    response_model=ExpenseInDB,
    summary="Подтвердить расход",
    description="Изменить статус расхода на 'confirmed'. Доступно: treasurer, admin.",
)
async def confirm_expense(
    expense_id: UUID,
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    db: AsyncSession = Depends(get_db),
) -> ExpenseInDB:
    """Подтвердить расход (смена статуса на "confirmed") (treasurer, admin)."""
    expense = await expense_service.confirm_expense(db, expense_id)
    return expense


@router.post(
    "/{expense_id}/cancel",
    response_model=ExpenseInDB,
    summary="Отменить расход",
    description="Изменить статус расхода на 'cancelled'. Доступно: treasurer, admin.",
)
async def cancel_expense(
    expense_id: UUID,
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    db: AsyncSession = Depends(get_db),
) -> ExpenseInDB:
    """Отменить расход (смена статуса на "cancelled") (treasurer, admin)."""
    expense = await expense_service.cancel_expense(db, expense_id)
    return expense
