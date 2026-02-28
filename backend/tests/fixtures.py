"""Pytest-фикстуры для переиспользования в тестах.

Все фикстуры создают одну сущность в переданной сессии (test_db) и возвращают её.
Зависимости между сущностями задаются через параметры фикстур (например,
sample_land_plot зависит от sample_cooperative).
"""

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Accrual,
    AppUser,
    ContributionType,
    Cooperative,
    Expense,
    ExpenseCategory,
    FinancialSubject,
    LandPlot,
    Meter,
    MeterReading,
    Owner,
    Payment,
    PlotOwnership,
)


@pytest_asyncio.fixture
async def sample_cooperative(test_db: AsyncSession) -> Cooperative:
    """Один СТ для тестов."""
    coop = Cooperative(name="СТ Тестовый", unp="999999999", address="г. Минск")
    test_db.add(coop)
    await test_db.flush()
    await test_db.refresh(coop)
    return coop


@pytest_asyncio.fixture
async def sample_owner(test_db: AsyncSession) -> Owner:
    """Один владелец (физ. лицо) для тестов."""
    owner = Owner(
        owner_type="physical",
        name="Тестов Тест Тестович",
        tax_id="111111111A",
        contact_phone="+375291234567",
    )
    test_db.add(owner)
    await test_db.flush()
    await test_db.refresh(owner)
    return owner


@pytest_asyncio.fixture
async def sample_land_plot(test_db: AsyncSession, sample_cooperative: Cooperative) -> LandPlot:
    """Один участок для тестов (привязан к sample_cooperative)."""
    plot = LandPlot(
        cooperative_id=sample_cooperative.id,
        plot_number="1",
        area_sqm=Decimal("600.00"),
        status="active",
    )
    test_db.add(plot)
    await test_db.flush()
    await test_db.refresh(plot)
    return plot


@pytest_asyncio.fixture
async def sample_plot_ownership(
    test_db: AsyncSession,
    sample_land_plot: LandPlot,
    sample_owner: Owner,
) -> PlotOwnership:
    """Одно право собственности на участок (основной владелец)."""
    po = PlotOwnership(
        land_plot_id=sample_land_plot.id,
        owner_id=sample_owner.id,
        share_numerator=1,
        share_denominator=1,
        is_primary=True,
        valid_from=date.today(),
        valid_to=None,
    )
    test_db.add(po)
    await test_db.flush()
    await test_db.refresh(po)
    return po


@pytest_asyncio.fixture
async def sample_contribution_type(test_db: AsyncSession) -> ContributionType:
    """Один вид взноса для тестов."""
    ct = ContributionType(name="Членский", code="MEMBER", description="Членский взнос")
    test_db.add(ct)
    await test_db.flush()
    await test_db.refresh(ct)
    return ct


@pytest_asyncio.fixture
async def sample_expense_category(test_db: AsyncSession) -> ExpenseCategory:
    """Одна категория расходов для тестов."""
    cat = ExpenseCategory(name="Дороги", code="ROADS", description="Ремонт дорог")
    test_db.add(cat)
    await test_db.flush()
    await test_db.refresh(cat)
    return cat


@pytest_asyncio.fixture
async def sample_financial_subject(
    test_db: AsyncSession,
    sample_land_plot: LandPlot,
    sample_cooperative: Cooperative,
) -> FinancialSubject:
    """Один финансовый субъект (участок) для тестов."""
    fs = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=sample_land_plot.id,
        cooperative_id=sample_cooperative.id,
        code="FS-TEST-001",
        status="active",
    )
    test_db.add(fs)
    await test_db.flush()
    await test_db.refresh(fs)
    return fs


@pytest_asyncio.fixture
async def sample_accrual(
    test_db: AsyncSession,
    sample_financial_subject: FinancialSubject,
    sample_contribution_type: ContributionType,
) -> Accrual:
    """Одно начисление для тестов."""
    today = date.today()
    accrual = Accrual(
        financial_subject_id=sample_financial_subject.id,
        contribution_type_id=sample_contribution_type.id,
        amount=Decimal("500.00"),
        accrual_date=today,
        period_start=today.replace(month=1, day=1),
        period_end=today,
        status="applied",
    )
    test_db.add(accrual)
    await test_db.flush()
    await test_db.refresh(accrual)
    return accrual


@pytest_asyncio.fixture
async def sample_payment(
    test_db: AsyncSession,
    sample_financial_subject: FinancialSubject,
    sample_owner: Owner,
) -> Payment:
    """Один платёж для тестов."""
    payment = Payment(
        financial_subject_id=sample_financial_subject.id,
        payer_owner_id=sample_owner.id,
        amount=Decimal("300.00"),
        payment_date=date.today(),
        document_number="П-1",
        status="confirmed",
    )
    test_db.add(payment)
    await test_db.flush()
    await test_db.refresh(payment)
    return payment


@pytest_asyncio.fixture
async def sample_expense(
    test_db: AsyncSession,
    sample_cooperative: Cooperative,
    sample_expense_category: ExpenseCategory,
) -> Expense:
    """Один расход для тестов."""
    expense = Expense(
        cooperative_id=sample_cooperative.id,
        category_id=sample_expense_category.id,
        amount=Decimal("5000.00"),
        expense_date=date.today(),
        description="Ремонт",
        status="confirmed",
    )
    test_db.add(expense)
    await test_db.flush()
    await test_db.refresh(expense)
    return expense


@pytest_asyncio.fixture
async def sample_meter(test_db: AsyncSession, sample_owner: Owner) -> Meter:
    """Один счётчик для тестов."""
    meter = Meter(
        owner_id=sample_owner.id,
        meter_type="ELECTRICITY",
        serial_number="M-001",
        installation_date=datetime.now(UTC),
        status="active",
    )
    test_db.add(meter)
    await test_db.flush()
    await test_db.refresh(meter)
    return meter


@pytest_asyncio.fixture
async def sample_meter_reading(test_db: AsyncSession, sample_meter: Meter) -> MeterReading:
    """Одно показание счётчика для тестов."""
    reading = MeterReading(
        meter_id=sample_meter.id,
        reading_value=Decimal("100.50"),
        reading_date=datetime.now(UTC),
    )
    test_db.add(reading)
    await test_db.flush()
    await test_db.refresh(reading)
    return reading


@pytest_asyncio.fixture
async def sample_app_user(test_db: AsyncSession, sample_cooperative: Cooperative) -> AppUser:
    """Один пользователь (казначей) для тестов, привязан к СТ."""
    from app.core.security import get_password_hash

    user = AppUser(
        username="treasurer_fixture",
        email="treasurer_fixture@example.com",
        hashed_password=get_password_hash("fixturepass"),
        role="treasurer",
        cooperative_id=sample_cooperative.id,
        is_active=True,
    )
    test_db.add(user)
    await test_db.flush()
    await test_db.refresh(user)
    return user
