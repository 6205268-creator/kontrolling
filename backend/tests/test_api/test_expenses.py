from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, get_password_hash
from app.models.app_user import AppUser
from app.models.cooperative import Cooperative
from app.models.expense import Expense
from app.models.expense_category import ExpenseCategory


@pytest.fixture
async def admin_token(test_db) -> str:
    """Создаёт admin пользователя и возвращает токен."""
    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    admin = AppUser(
        username="admin_user",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass"),
        role="admin",
        is_active=True,
    )
    test_db.add(admin)
    await test_db.commit()

    return create_access_token(data={"sub": "admin_user", "role": "admin"})


@pytest.fixture
async def treasurer_token(test_db) -> str:
    """Создаёт treasurer пользователя с СТ и возвращает токен."""
    coop = Cooperative(name="СТ Казначея")
    test_db.add(coop)
    await test_db.flush()

    treasurer = AppUser(
        username="treasurer_user",
        email="treasurer@example.com",
        hashed_password=get_password_hash("treasurerpass"),
        role="treasurer",
        cooperative_id=coop.id,
        is_active=True,
    )
    test_db.add(treasurer)
    await test_db.commit()

    return create_access_token(data={"sub": "treasurer_user", "role": "treasurer"})


@pytest.fixture
async def expense_category_fixture(test_db) -> ExpenseCategory:
    """Создаёт категорию расходов."""
    category = ExpenseCategory(
        name="Дороги",
        code="ROADS",
        description="Ремонт и содержание дорог",
    )
    test_db.add(category)
    await test_db.commit()
    return category


@pytest.mark.asyncio
async def test_get_expense_categories(
    async_client: AsyncClient,
    admin_token: str,
    expense_category_fixture: ExpenseCategory,
) -> None:
    """Тест получения списка категорий расходов."""
    response = await async_client.get(
        "/api/v1/expenses/categories",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Дороги"
    assert data[0]["code"] == "ROADS"


@pytest.mark.asyncio
async def test_create_expense(
    async_client: AsyncClient,
    admin_token: str,
    expense_category_fixture: ExpenseCategory,
    test_db,
) -> None:
    """Тест создания расхода."""
    coop = Cooperative(name="СТ Для расходов")
    test_db.add(coop)
    await test_db.commit()

    response = await async_client.post(
        "/api/v1/expenses/",
        json={
            "cooperative_id": str(coop.id),
            "category_id": str(expense_category_fixture.id),
            "amount": "50000.00",
            "expense_date": str(date.today()),
            "document_number": "РКО-001",
            "description": "Ремонт дороги",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == "50000.00"
    assert data["status"] == "created"
    assert data["document_number"] == "РКО-001"


@pytest.mark.asyncio
async def test_confirm_expense(
    async_client: AsyncClient,
    admin_token: str,
    expense_category_fixture: ExpenseCategory,
    test_db,
) -> None:
    """Тест подтверждения расхода (created → confirmed)."""
    coop = Cooperative(name="СТ Для подтверждения")
    test_db.add(coop)
    await test_db.flush()

    expense = Expense(
        cooperative_id=coop.id,
        category_id=expense_category_fixture.id,
        amount=Decimal("10000.00"),
        expense_date=date.today(),
        status="created",
    )
    test_db.add(expense)
    await test_db.commit()

    response = await async_client.post(
        f"/api/v1/expenses/{expense.id}/confirm",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"


@pytest.mark.asyncio
async def test_cancel_expense(
    async_client: AsyncClient,
    admin_token: str,
    expense_category_fixture: ExpenseCategory,
    test_db,
) -> None:
    """Тест отмены расхода (confirmed → cancelled)."""
    coop = Cooperative(name="СТ Для отмены")
    test_db.add(coop)
    await test_db.flush()

    expense = Expense(
        cooperative_id=coop.id,
        category_id=expense_category_fixture.id,
        amount=Decimal("10000.00"),
        expense_date=date.today(),
        status="confirmed",
    )
    test_db.add(expense)
    await test_db.commit()

    response = await async_client.post(
        f"/api/v1/expenses/{expense.id}/cancel",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_already_cancelled_expense(
    async_client: AsyncClient,
    admin_token: str,
    expense_category_fixture: ExpenseCategory,
    test_db,
) -> None:
    """Тест 400 при попытке отменить уже отменённый расход."""
    coop = Cooperative(name="СТ Для отмены 2")
    test_db.add(coop)
    await test_db.flush()

    expense = Expense(
        cooperative_id=coop.id,
        category_id=expense_category_fixture.id,
        amount=Decimal("10000.00"),
        expense_date=date.today(),
        status="cancelled",
    )
    test_db.add(expense)
    await test_db.commit()

    response = await async_client.post(
        f"/api/v1/expenses/{expense.id}/cancel",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_confirm_non_created_expense(
    async_client: AsyncClient,
    admin_token: str,
    expense_category_fixture: ExpenseCategory,
    test_db,
) -> None:
    """Тест 400 при попытке подтвердить уже подтверждённый расход."""
    coop = Cooperative(name="СТ Для подтверждения 2")
    test_db.add(coop)
    await test_db.flush()

    expense = Expense(
        cooperative_id=coop.id,
        category_id=expense_category_fixture.id,
        amount=Decimal("10000.00"),
        expense_date=date.today(),
        status="confirmed",
    )
    test_db.add(expense)
    await test_db.commit()

    response = await async_client.post(
        f"/api/v1/expenses/{expense.id}/confirm",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_expenses_by_cooperative(
    async_client: AsyncClient,
    admin_token: str,
    expense_category_fixture: ExpenseCategory,
    test_db,
) -> None:
    """Тест получения расходов по СТ."""
    coop = Cooperative(name="СТ Для списка расходов")
    test_db.add(coop)
    await test_db.flush()

    # Создаём несколько расходов
    for amount in [Decimal("1000.00"), Decimal("2000.00"), Decimal("3000.00")]:
        expense = Expense(
            cooperative_id=coop.id,
            category_id=expense_category_fixture.id,
            amount=amount,
            expense_date=date.today(),
            status="confirmed",
        )
        test_db.add(expense)

    await test_db.commit()

    response = await async_client.get(
        "/api/v1/expenses/",
        params={"cooperative_id": str(coop.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_create_expense_forbidden_for_other_cooperative(
    async_client: AsyncClient,
    treasurer_token: str,
    expense_category_fixture: ExpenseCategory,
    test_db,
) -> None:
    """Тест 403 при попытке создать расход для чужого СТ."""
    # Создаём другое СТ
    other_coop = Cooperative(name="Чужое СТ")
    test_db.add(other_coop)
    await test_db.commit()

    response = await async_client.post(
        "/api/v1/expenses/",
        json={
            "cooperative_id": str(other_coop.id),
            "category_id": str(expense_category_fixture.id),
            "amount": "10000.00",
            "expense_date": str(date.today()),
        },
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_expense_invalid_amount(
    async_client: AsyncClient,
    admin_token: str,
    expense_category_fixture: ExpenseCategory,
    test_db,
) -> None:
    """Тест 422 при сумме <= 0."""
    coop = Cooperative(name="СТ Для невалидного")
    test_db.add(coop)
    await test_db.commit()

    response = await async_client.post(
        "/api/v1/expenses/",
        json={
            "cooperative_id": str(coop.id),
            "category_id": str(expense_category_fixture.id),
            "amount": "0.00",  # Неvalid
            "expense_date": str(date.today()),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_expenses_missing_cooperative_id(
    async_client: AsyncClient,
    treasurer_token: str,
) -> None:
    """Тест что treasurer без cooperative_id получает список своего СТ."""
    response = await async_client.get(
        "/api/v1/expenses/",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    # Для treasurer cooperative_id подставляется автоматически
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_expense_category_not_found(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
) -> None:
    """Тест 404 при создании расхода с несуществующей категорией."""
    import uuid
    coop = Cooperative(name="СТ Для категории")
    test_db.add(coop)
    await test_db.commit()

    response = await async_client.post(
        "/api/v1/expenses/",
        json={
            "cooperative_id": str(coop.id),
            "category_id": str(uuid.uuid4()),  # Не существует
            "amount": "1000.00",
            "expense_date": str(date.today()),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404
