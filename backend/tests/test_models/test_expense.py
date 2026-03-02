from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cooperative_core.infrastructure.models import CooperativeModel as Cooperative
from app.modules.expenses.infrastructure.models import ExpenseModel as Expense
from app.modules.expenses.infrastructure.models import ExpenseCategoryModel as ExpenseCategory


@pytest.mark.asyncio
async def test_create_expense_category(test_db: AsyncSession) -> None:
    """Создание ExpenseCategory."""
    cat = ExpenseCategory(name="Дороги", code="ROADS", description="Ремонт дорог")
    test_db.add(cat)
    await test_db.commit()
    await test_db.refresh(cat)

    assert cat.id is not None
    assert cat.name == "Дороги"
    assert cat.code == "ROADS"
    assert cat.description == "Ремонт дорог"
    assert cat.created_at is not None
    assert isinstance(cat.created_at, datetime)


@pytest.mark.asyncio
async def test_create_expense_with_cooperative_and_category(test_db: AsyncSession) -> None:
    """Создание Expense с привязкой к Cooperative и ExpenseCategory."""
    coop = Cooperative(name="СТ Ромашка")
    cat = ExpenseCategory(name="Зарплата", code="SALARY")
    test_db.add_all([coop, cat])
    await test_db.flush()

    expense = Expense(
        cooperative_id=coop.id,
        category_id=cat.id,
        amount=Decimal("500.00"),
        expense_date=date(2026, 2, 15),
        document_number="ПП-101",
        description="Зарплата председателя за февраль",
        status="created",
    )
    test_db.add(expense)
    await test_db.commit()
    await test_db.refresh(expense)

    assert expense.id is not None
    assert expense.cooperative_id == coop.id
    assert expense.category_id == cat.id
    assert expense.amount == Decimal("500.00")
    assert expense.expense_date == date(2026, 2, 15)
    assert expense.document_number == "ПП-101"
    assert expense.description == "Зарплата председателя за февраль"
    assert expense.status == "created"
    assert expense.created_at is not None
    assert expense.updated_at is not None


@pytest.mark.asyncio
async def test_expense_statuses_created_confirmed_cancelled(test_db: AsyncSession) -> None:
    """Проверка статусов: created → confirmed → cancelled."""
    coop = Cooperative(name="СТ Тест")
    cat = ExpenseCategory(name="Материалы", code="MATERIALS")
    test_db.add_all([coop, cat])
    await test_db.flush()

    expense = Expense(
        cooperative_id=coop.id,
        category_id=cat.id,
        amount=Decimal("100.00"),
        expense_date=date(2026, 2, 1),
        status="created",
    )
    test_db.add(expense)
    await test_db.commit()
    await test_db.refresh(expense)

    assert expense.status == "created"
    expense.status = "confirmed"
    await test_db.commit()
    await test_db.refresh(expense)
    assert expense.status == "confirmed"
    expense.status = "cancelled"
    await test_db.commit()
    await test_db.refresh(expense)
    assert expense.status == "cancelled"


@pytest.mark.asyncio
async def test_expense_amount_positive_required(test_db: AsyncSession) -> None:
    """Валидация amount > 0: положительная сумма сохраняется."""
    coop = Cooperative(name="СТ Тест")
    cat = ExpenseCategory(name="Прочее", code="OTHER")
    test_db.add_all([coop, cat])
    await test_db.flush()

    expense = Expense(
        cooperative_id=coop.id,
        category_id=cat.id,
        amount=Decimal("0.01"),
        expense_date=date(2026, 2, 1),
        status="created",
    )
    test_db.add(expense)
    await test_db.commit()
    await test_db.refresh(expense)
    assert expense.amount == Decimal("0.01")


@pytest.mark.asyncio
async def test_expense_amount_zero_rejected(test_db: AsyncSession) -> None:
    """Валидация amount > 0: ноль отклоняется БД."""
    coop = Cooperative(name="СТ Тест")
    cat = ExpenseCategory(name="Прочее", code="OTHER2")
    test_db.add_all([coop, cat])
    await test_db.flush()

    expense = Expense(
        cooperative_id=coop.id,
        category_id=cat.id,
        amount=Decimal("0.00"),
        expense_date=date(2026, 2, 1),
        status="created",
    )
    test_db.add(expense)
    with pytest.raises(IntegrityError):
        await test_db.commit()
    await test_db.rollback()
