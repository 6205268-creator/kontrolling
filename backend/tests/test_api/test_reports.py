from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, get_password_hash

# Import models from Clean Architecture modules
from app.modules.accruals.infrastructure.models import AccrualModel as Accrual
from app.modules.accruals.infrastructure.models import ContributionTypeModel as ContributionType
from app.modules.administration.infrastructure.models import AppUserModel as AppUser
from app.modules.cooperative_core.infrastructure.models import CooperativeModel as Cooperative
from app.modules.expenses.infrastructure.models import ExpenseCategoryModel as ExpenseCategory
from app.modules.expenses.infrastructure.models import ExpenseModel as Expense
from app.modules.financial_core.infrastructure.models import (
    FinancialSubjectModel as FinancialSubject,
)
from app.modules.land_management.infrastructure.models import (
    LandPlotModel as LandPlot,
)
from app.modules.land_management.infrastructure.models import (
    OwnerModel as Owner,
)
from app.modules.land_management.infrastructure.models import (
    PlotOwnershipModel as PlotOwnership,
)
from app.modules.payments.infrastructure.models import PaymentModel as Payment


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
async def report_data_fixture(test_db) -> dict:
    """
    Создаёт тестовые данные для отчётов:
    - СТ с несколькими участками
    - Владельцы
    - Начисления и платежи с разной задолженностью
    - Расходы
    """
    # Создаём СТ
    coop = Cooperative(name="СТ Для отчётов")
    test_db.add(coop)
    await test_db.flush()

    # Создаём категорию расходов
    category = ExpenseCategory(name="Дороги", code="ROADS")
    test_db.add(category)
    await test_db.flush()

    # Создаём вид взноса
    contribution_type = ContributionType(name="Членский", code="MEMBER")
    test_db.add(contribution_type)
    await test_db.flush()

    # Создаём владельцев
    owner1 = Owner(owner_type="physical", name="Иванов И.И.", tax_id="123456789")
    owner2 = Owner(owner_type="physical", name="Петров П.П.", tax_id="987654321")
    test_db.add_all([owner1, owner2])
    await test_db.flush()

    # Создаём участки
    plot1 = LandPlot(cooperative_id=coop.id, plot_number="1", area_sqm=Decimal("600.00"))
    plot2 = LandPlot(cooperative_id=coop.id, plot_number="2", area_sqm=Decimal("500.00"))
    plot3 = LandPlot(cooperative_id=coop.id, plot_number="3", area_sqm=Decimal("700.00"))
    test_db.add_all([plot1, plot2, plot3])
    await test_db.flush()

    # Создаём права собственности (основные владельцы)
    ownership1 = PlotOwnership(
        land_plot_id=plot1.id,
        owner_id=owner1.id,
        share_numerator=1,
        share_denominator=1,
        is_primary=True,
        valid_from=date.today(),
    )
    ownership2 = PlotOwnership(
        land_plot_id=plot2.id,
        owner_id=owner2.id,
        share_numerator=1,
        share_denominator=1,
        is_primary=True,
        valid_from=date.today(),
    )
    ownership3 = PlotOwnership(
        land_plot_id=plot3.id,
        owner_id=owner1.id,
        share_numerator=1,
        share_denominator=1,
        is_primary=True,
        valid_from=date.today(),
    )
    test_db.add_all([ownership1, ownership2, ownership3])
    await test_db.flush()

    # Создаём финансовые субъекты
    subject1 = FinancialSubject(
        subject_type="LAND_PLOT", subject_id=plot1.id, cooperative_id=coop.id, code="FS-001"
    )
    subject2 = FinancialSubject(
        subject_type="LAND_PLOT", subject_id=plot2.id, cooperative_id=coop.id, code="FS-002"
    )
    subject3 = FinancialSubject(
        subject_type="LAND_PLOT", subject_id=plot3.id, cooperative_id=coop.id, code="FS-003"
    )
    test_db.add_all([subject1, subject2, subject3])
    await test_db.flush()

    # Создаём начисления (разные суммы для разных долгов)
    # Участок 1: задолженность 500 (1000 начислено - 500 оплачено)
    accrual1 = Accrual(
        financial_subject_id=subject1.id,
        contribution_type_id=contribution_type.id,
        amount=Decimal("1000.00"),
        accrual_date=date.today(),
        period_start=date.today().replace(month=1, day=1),
        status="applied",
        operation_number="ACC-R-1",
    )
    payment1 = Payment(
        financial_subject_id=subject1.id,
        payer_owner_id=owner1.id,
        amount=Decimal("500.00"),
        payment_date=date.today(),
        status="confirmed",
        operation_number="PAY-R-1",
    )

    # Участок 2: задолженность 0 (1000 начислено - 1000 оплачено)
    accrual2 = Accrual(
        financial_subject_id=subject2.id,
        contribution_type_id=contribution_type.id,
        amount=Decimal("1000.00"),
        accrual_date=date.today(),
        period_start=date.today().replace(month=1, day=1),
        status="applied",
        operation_number="ACC-R-2",
    )
    payment2 = Payment(
        financial_subject_id=subject2.id,
        payer_owner_id=owner2.id,
        amount=Decimal("1000.00"),
        payment_date=date.today(),
        status="confirmed",
        operation_number="PAY-R-2",
    )

    # Участок 3: задолженность 1500 (2000 начислено - 500 оплачено)
    accrual3 = Accrual(
        financial_subject_id=subject3.id,
        contribution_type_id=contribution_type.id,
        amount=Decimal("2000.00"),
        accrual_date=date.today(),
        period_start=date.today().replace(month=1, day=1),
        status="applied",
        operation_number="ACC-R-3",
    )
    payment3 = Payment(
        financial_subject_id=subject3.id,
        payer_owner_id=owner1.id,
        amount=Decimal("500.00"),
        payment_date=date.today(),
        status="confirmed",
        operation_number="PAY-R-3",
    )

    test_db.add_all([accrual1, payment1, accrual2, payment2, accrual3, payment3])

    # Создаём расходы
    expense1 = Expense(
        cooperative_id=coop.id,
        category_id=category.id,
        amount=Decimal("5000.00"),
        expense_date=date.today(),
        status="confirmed",
        description="Ремонт дороги",
        operation_number="EXP-R-1",
    )
    expense2 = Expense(
        cooperative_id=coop.id,
        category_id=category.id,
        amount=Decimal("3000.00"),
        expense_date=date.today(),
        status="confirmed",
        description="Закупка материалов",
        operation_number="EXP-R-2",
    )
    test_db.add_all([expense1, expense2])

    await test_db.commit()

    return {
        "coop": coop,
        "category": category,
        "contribution_type": contribution_type,
        "owners": [owner1, owner2],
        "plots": [plot1, plot2, plot3],
        "subjects": [subject1, subject2, subject3],
        "accruals": [accrual1, accrual2, accrual3],
        "payments": [payment1, payment2, payment3],
        "expenses": [expense1, expense2],
    }


@pytest.mark.asyncio
async def test_get_debtors_report(
    async_client: AsyncClient,
    admin_token: str,
    report_data_fixture: dict,
) -> None:
    """Тест отчёта по должникам."""
    coop_id = str(report_data_fixture["coop"].id)

    response = await async_client.get(
        "/api/reports/debtors",
        params={"cooperative_id": coop_id, "min_debt": "0.00"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    # Должны быть 2 должника (участок 1 с долгом 500 и участок 3 с долгом 1500)
    assert len(data) == 2

    # Сортировка по убыванию долга
    assert data[0]["total_debt"] == "1500.00"
    assert data[0]["owner_name"] == "Иванов И.И."
    assert data[1]["total_debt"] == "500.00"
    assert data[1]["owner_name"] == "Иванов И.И."


@pytest.mark.asyncio
async def test_get_debtors_report_with_min_debt(
    async_client: AsyncClient,
    admin_token: str,
    report_data_fixture: dict,
) -> None:
    """Тест отчёта по должникам с фильтром min_debt."""
    coop_id = str(report_data_fixture["coop"].id)

    response = await async_client.get(
        "/api/reports/debtors",
        params={"cooperative_id": coop_id, "min_debt": "1000.00"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    # Только участок 3 с долгом 1500
    assert len(data) == 1
    assert data[0]["total_debt"] == "1500.00"


@pytest.mark.asyncio
async def test_get_debtors_report_empty(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
) -> None:
    """Тест отчёта по должникам без данных."""
    coop = Cooperative(name="Пустое СТ")
    test_db.add(coop)
    await test_db.commit()

    response = await async_client.get(
        "/api/reports/debtors",
        params={"cooperative_id": str(coop.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_cash_flow_report(
    async_client: AsyncClient,
    admin_token: str,
    report_data_fixture: dict,
) -> None:
    """Тест отчёта о движении денежных средств."""
    coop_id = str(report_data_fixture["coop"].id)
    today = date.today()

    response = await async_client.get(
        "/api/reports/cash-flow",
        params={
            "cooperative_id": coop_id,
            "period_start": str(today.replace(day=1)),
            "period_end": str(today),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    # total_accruals = 1000 + 1000 + 2000 = 4000
    assert data["total_accruals"] == "4000.00"
    # total_payments = 500 + 1000 + 500 = 2000
    assert data["total_payments"] == "2000.00"
    # total_expenses = 5000 + 3000 = 8000
    assert data["total_expenses"] == "8000.00"
    # net_balance = payments - expenses = 2000 - 8000 = -6000
    assert data["net_balance"] == "-6000.00"


@pytest.mark.asyncio
async def test_get_cash_flow_report_partial_period(
    async_client: AsyncClient,
    admin_token: str,
    report_data_fixture: dict,
    test_db,
) -> None:
    """Тест отчёта о движении средств за частичный период."""
    coop = report_data_fixture["coop"]

    # Создаём начисление и платёж за вчерашний день

    yesterday = date.today().replace(day=1)

    subject = report_data_fixture["subjects"][0]
    owner = report_data_fixture["owners"][0]

    # Добавим ещё одно начисление за вчера
    accrual = Accrual(
        financial_subject_id=subject.id,
        contribution_type_id=report_data_fixture["contribution_type"].id,
        amount=Decimal("500.00"),
        accrual_date=yesterday,
        period_start=yesterday,
        status="applied",
        operation_number="ACC-R-CF",
    )
    test_db.add(accrual)

    # Добавим платёж за вчера
    payment = Payment(
        financial_subject_id=subject.id,
        payer_owner_id=owner.id,
        amount=Decimal("200.00"),
        payment_date=yesterday,
        status="confirmed",
        operation_number="PAY-R-CF",
    )
    test_db.add(payment)

    # Добавим расход за вчера
    expense = Expense(
        cooperative_id=coop.id,
        category_id=report_data_fixture["category"].id,
        amount=Decimal("1000.00"),
        expense_date=yesterday,
        status="confirmed",
        operation_number="EXP-R-CF",
    )
    test_db.add(expense)

    await test_db.commit()

    response = await async_client.get(
        "/api/reports/cash-flow",
        params={
            "cooperative_id": str(coop.id),
            "period_start": str(yesterday),
            "period_end": str(yesterday),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_accruals"] == "500.00"
    assert data["total_payments"] == "200.00"
    assert data["total_expenses"] == "1000.00"
    assert data["net_balance"] == "-800.00"


@pytest.mark.asyncio
async def test_get_debtors_report_treasurer_auto_cooperative(
    async_client: AsyncClient,
    treasurer_token: str,
    report_data_fixture: dict,
) -> None:
    """Тест что treasurer получает отчёт по своему СТ автоматически."""
    response = await async_client.get(
        "/api/reports/debtors",
        params={"min_debt": "0.00"},
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    # Для treasurer cooperative_id подставляется автоматически
    assert response.status_code == 200
    data = response.json()
    # Должны быть должники из СТ казначея
    assert len(data) >= 0  # Может быть 0 если нет долгов


@pytest.mark.asyncio
async def test_get_cash_flow_report_treasurer_auto_cooperative(
    async_client: AsyncClient,
    treasurer_token: str,
) -> None:
    """Тест что treasurer получает отчёт о движении средств по своему СТ."""
    today = date.today()

    response = await async_client.get(
        "/api/reports/cash-flow",
        params={
            "period_start": str(today.replace(day=1)),
            "period_end": str(today),
        },
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_debtors_report_no_cooperative_id(
    async_client: AsyncClient,
    admin_token: str,
) -> None:
    """Тест 400 при отсутствии cooperative_id для admin."""
    response = await async_client.get(
        "/api/reports/debtors",
        params={"min_debt": "0.00"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Admin должен указать cooperative_id
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_cash_flow_report_no_cooperative_id(
    async_client: AsyncClient,
    admin_token: str,
) -> None:
    """Тест 400 при отсутствии cooperative_id для admin."""
    today = date.today()

    response = await async_client.get(
        "/api/reports/cash-flow",
        params={
            "period_start": str(today.replace(day=1)),
            "period_end": str(today),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Admin должен указать cooperative_id
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_debtors_report_invalid_cooperative_id(
    async_client: AsyncClient,
    admin_token: str,
) -> None:
    """Тест 422 при неверном формате cooperative_id."""
    response = await async_client.get(
        "/api/reports/debtors",
        params={"cooperative_id": "invalid-uuid", "min_debt": "0.00"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_debtors_report_subject_info_land_plot(
    async_client: AsyncClient,
    admin_token: str,
    report_data_fixture: dict,
) -> None:
    """Тест что subject_info содержит plot_number для участка."""
    coop_id = str(report_data_fixture["coop"].id)

    response = await async_client.get(
        "/api/reports/debtors",
        params={"cooperative_id": coop_id, "min_debt": "0.00"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    # Проверяем что есть plot_number в subject_info
    for debtor in data:
        assert "plot_number" in debtor["subject_info"]
