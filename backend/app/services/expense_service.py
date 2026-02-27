from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import Expense
from app.models.expense_category import ExpenseCategory
from app.schemas.expense import ExpenseCreate


async def create_expense(db: AsyncSession, expense_data: ExpenseCreate) -> Expense:
    """
    Создание расхода.

    При создании статус = "created".
    """
    db_expense = Expense(
        cooperative_id=expense_data.cooperative_id,
        category_id=expense_data.category_id,
        amount=expense_data.amount,
        expense_date=expense_data.expense_date,
        document_number=expense_data.document_number,
        description=expense_data.description,
        status="created",
    )
    db.add(db_expense)
    await db.commit()
    await db.refresh(db_expense)
    return db_expense


async def get_expense(db: AsyncSession, expense_id: UUID) -> Expense | None:
    """Получение расхода по ID."""
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    return result.scalar_one_or_none()


async def confirm_expense(db: AsyncSession, expense_id: UUID) -> Expense:
    """
    Подтверждение расхода (смена статуса на "confirmed").

    Подтверждается расход со статусом "created".
    """
    expense = await get_expense(db, expense_id)
    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Расход не найден",
        )

    if expense.status != "created":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Нельзя подтвердить расход со статусом '{expense.status}'. Только статус 'created'.",
        )

    expense.status = "confirmed"
    await db.commit()
    await db.refresh(expense)
    return expense


async def cancel_expense(db: AsyncSession, expense_id: UUID) -> Expense:
    """
    Отмена расхода (смена статуса на "cancelled").

    Отменяется расход со статусом "created" или "confirmed".
    """
    expense = await get_expense(db, expense_id)
    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Расход не найден",
        )

    if expense.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Расход уже отменён",
        )

    expense.status = "cancelled"
    await db.commit()
    await db.refresh(expense)
    return expense


async def get_expenses_by_cooperative(
    db: AsyncSession,
    cooperative_id: UUID,
) -> list[Expense]:
    """Получение списка расходов по СТ."""
    result = await db.execute(
        select(Expense)
        .where(Expense.cooperative_id == cooperative_id)
        .order_by(Expense.expense_date.desc())
    )
    return list(result.scalars().all())


async def get_expense_categories(db: AsyncSession) -> list[ExpenseCategory]:
    """Получение списка категорий расходов."""
    result = await db.execute(
        select(ExpenseCategory).order_by(ExpenseCategory.name)
    )
    return list(result.scalars().all())


async def get_expense_category(db: AsyncSession, category_id: UUID) -> ExpenseCategory | None:
    """Получение категории расхода по ID."""
    result = await db.execute(
        select(ExpenseCategory).where(ExpenseCategory.id == category_id)
    )
    return result.scalar_one_or_none()
