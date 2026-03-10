from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cooperative_core.infrastructure.models import CooperativeModel as Cooperative
from app.modules.expenses.infrastructure.models import ExpenseCategoryModel as ExpenseCategory
from app.modules.expenses.infrastructure.models import ExpenseModel as Expense


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
        operation_number="EXP-M-1",
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
        operation_number="EXP-M-2",
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
        operation_number="EXP-M-3",
    )
    test_db.add(expense)
    await test_db.flush()


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
        operation_number="EXP-M-4",
    )
    test_db.add(expense)
    with pytest.raises(IntegrityError):
        await test_db.commit()
    await test_db.rollback()


@pytest.mark.asyncio
async def test_expense_amount_immutable_on_update(test_db: AsyncSession) -> None:
    """Этап 4: amount не изменяется при update (immutability)."""
    from app.modules.expenses.domain.entities import Expense as ExpenseEntity
    from app.modules.expenses.infrastructure.repositories import ExpenseRepository

    coop = Cooperative(name="СТ Тест")
    cat = ExpenseCategory(name="Тест", code="TEST")
    test_db.add_all([coop, cat])
    await test_db.flush()

    original_amount = Decimal("100.00")
    expense_model = Expense(
        cooperative_id=coop.id,
        category_id=cat.id,
        amount=original_amount,
        expense_date=date(2026, 2, 1),
        status="created",
        operation_number="EXP-M-5",
    )
    test_db.add(expense_model)
    await test_db.commit()
    await test_db.refresh(expense_model)

    # Создаём domain entity с изменённым amount (не из сессии)
    entity = ExpenseEntity(
        id=expense_model.id,
        cooperative_id=expense_model.cooperative_id,
        category_id=expense_model.category_id,
        amount=Decimal("999.99"),  # Пытаемся изменить amount
        expense_date=expense_model.expense_date,
        document_number=expense_model.document_number,
        description=expense_model.description,
        status=expense_model.status,
        operation_number=expense_model.operation_number,
    )

    repo = ExpenseRepository(test_db)
    updated = await repo.update(entity)

    # amount должен остаться оригинальным (не обновляться в БД)
    assert updated.amount == original_amount, "Amount should be immutable - not updated in repository"
