import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Использовать SQLite для тестов
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.db.base import Base
import app.models  # noqa: F401
from app.main import app
from app.core.security import get_password_hash


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    from app.api import deps
    from app.db import session as db_session

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db

    app.dependency_overrides[deps.get_db] = override_get_db
    app.dependency_overrides[db_session.get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_cooperative(test_db: AsyncSession) -> app.models.Cooperative:
    """Создаёт тестовое СТ."""
    cooperative = app.models.Cooperative(
        id=uuid4(),
        name="Тестовое СТ Ромашка",
        unp="123456789",
        address="тестовый адрес",
    )
    test_db.add(cooperative)
    await test_db.commit()
    await test_db.refresh(cooperative)
    return cooperative


@pytest_asyncio.fixture
async def test_owner(test_db: AsyncSession) -> app.models.Owner:
    """Создаёт тестового владельца."""
    owner = app.models.Owner(
        id=uuid4(),
        owner_type="physical",
        name="Иванов Иван Иванович",
        tax_id="123456789",
        contact_email="test@example.com",
    )
    test_db.add(owner)
    await test_db.commit()
    await test_db.refresh(owner)
    return owner


@pytest_asyncio.fixture
async def test_user(test_db: AsyncSession, test_cooperative: app.models.Cooperative) -> app.models.AppUser:
    """Создаёт тестового пользователя с ролью treasurer."""
    user = app.models.AppUser(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        role="treasurer",
        cooperative_id=test_cooperative.id,
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_land_plot(
    test_db: AsyncSession,
    test_cooperative: app.models.Cooperative,
    test_owner: app.models.Owner,
) -> app.models.LandPlot:
    """Создаёт тестовый участок с владельцем."""
    land_plot = app.models.LandPlot(
        id=uuid4(),
        cooperative_id=test_cooperative.id,
        plot_number="123",
        area_sqm=Decimal("600.00"),
        status="active",
    )
    test_db.add(land_plot)
    await test_db.commit()
    await test_db.refresh(land_plot)

    ownership = app.models.PlotOwnership(
        id=uuid4(),
        land_plot_id=land_plot.id,
        owner_id=test_owner.id,
        share_numerator=1,
        share_denominator=1,
        is_primary=True,
        valid_from=date.today(),
    )
    test_db.add(ownership)
    await test_db.commit()

    return land_plot


@pytest_asyncio.fixture
async def test_financial_subject(
    test_db: AsyncSession,
    test_cooperative: app.models.Cooperative,
    test_land_plot: app.models.LandPlot,
) -> app.models.FinancialSubject:
    """Создаёт тестовый финансовый субъект для участка."""
    subject = app.models.FinancialSubject(
        id=uuid4(),
        subject_type="LAND_PLOT",
        subject_id=test_land_plot.id,
        cooperative_id=test_cooperative.id,
        code=f"FS-{str(uuid4())[:8]}",
        status="active",
    )
    test_db.add(subject)
    await test_db.commit()
    await test_db.refresh(subject)
    return subject


@pytest_asyncio.fixture
async def test_contribution_type(test_db: AsyncSession) -> app.models.ContributionType:
    """Создаёт тестовый тип взноса."""
    contribution = app.models.ContributionType(
        id=uuid4(),
        name="Членский взнос",
        code="MEMBER",
        description="Ежемесячный членский взнос",
    )
    test_db.add(contribution)
    await test_db.commit()
    await test_db.refresh(contribution)
    return contribution


@pytest_asyncio.fixture
async def test_accrual(
    test_db: AsyncSession,
    test_financial_subject: app.models.FinancialSubject,
    test_contribution_type: app.models.ContributionType,
) -> app.models.Accrual:
    """Создаёт тестовое начисление."""
    accrual = app.models.Accrual(
        id=uuid4(),
        financial_subject_id=test_financial_subject.id,
        contribution_type_id=test_contribution_type.id,
        amount=Decimal("100.00"),
        accrual_date=date.today(),
        period_start=date.today().replace(day=1),
        period_end=date.today(),
        status="applied",
    )
    test_db.add(accrual)
    await test_db.commit()
    await test_db.refresh(accrual)
    return accrual


@pytest_asyncio.fixture
async def test_payment(
    test_db: AsyncSession,
    test_financial_subject: app.models.FinancialSubject,
    test_owner: app.models.Owner,
) -> app.models.Payment:
    """Создаёт тестовый платёж."""
    payment = app.models.Payment(
        id=uuid4(),
        financial_subject_id=test_financial_subject.id,
        payer_owner_id=test_owner.id,
        amount=Decimal("50.00"),
        payment_date=date.today(),
        status="confirmed",
    )
    test_db.add(payment)
    await test_db.commit()
    await test_db.refresh(payment)
    return payment


@pytest.fixture
def test_user_credentials() -> dict:
    """Возвращает credentials для тестового пользователя."""
    return {"username": "testuser", "password": "testpassword123"}
