"""Fixtures for Payment Distribution module tests.

When tests are collected only from this package, test_db and admin_token
are defined here so that no dependency on backend/tests/conftest.py is needed.
When running pytest with both tests/ and this package, this conftest's
async_client overrides the root one for tests in this package.
"""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Использовать SQLite для тестов (как в backend/tests/conftest.py)
TEST_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# Импорт моделей до app, чтобы Base.metadata содержал все таблицы
import app.modules.accruals.infrastructure.models  # noqa: F401
import app.modules.administration.infrastructure.models  # noqa: F401
import app.modules.cooperative_core.infrastructure.models  # noqa: F401
import app.modules.expenses.infrastructure.models  # noqa: F401
import app.modules.financial_core.infrastructure.models  # noqa: F401
import app.modules.land_management.infrastructure.models  # noqa: F401
import app.modules.meters.infrastructure.models  # noqa: F401
import app.modules.payment_distribution.infrastructure.models  # noqa: F401
import app.modules.payments.infrastructure.models  # noqa: F401
from app.db.base import Base
from app.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Event loop for session-scoped tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Сессия БД для тестов с созданными таблицами всех модулей."""
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


@pytest_asyncio.fixture
async def sample_cooperative(test_db: AsyncSession):
    """Один СТ для тестов API."""
    from app.modules.cooperative_core.infrastructure.models import CooperativeModel

    coop = CooperativeModel(name="СТ Тестовый", unp="999999999", address="г. Минск")
    test_db.add(coop)
    await test_db.flush()
    await test_db.refresh(coop)
    return coop


@pytest_asyncio.fixture
async def sample_owner(test_db: AsyncSession):
    """Один владелец для тестов API."""
    from app.modules.land_management.infrastructure.models import OwnerModel

    owner = OwnerModel(
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
async def admin_token(test_db: AsyncSession) -> str:
    """Создаёт admin пользователя и возвращает JWT (как в tests/test_api)."""
    from app.core.security import create_access_token, get_password_hash
    from app.modules.administration.infrastructure.models import AppUserModel as AppUser
    from app.modules.cooperative_core.infrastructure.models import CooperativeModel as Cooperative

    coop = Cooperative(name="СТ Тест Payment Distribution")
    test_db.add(coop)
    await test_db.flush()

    admin = AppUser(
        username="admin_pd",
        email="admin_pd@example.com",
        hashed_password=get_password_hash("adminpass"),
        role="admin",
        is_active=True,
    )
    test_db.add(admin)
    await test_db.commit()

    return create_access_token(data={"sub": "admin_pd", "role": "admin"})


@pytest_asyncio.fixture
async def async_client(
    test_db: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient с base_url на /api/payment-distribution и подменённым get_db."""
    from app.api import deps
    from app.db import session as db_session

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db

    app.dependency_overrides[deps.get_db] = override_get_db
    app.dependency_overrides[db_session.get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test/api/payment-distribution",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
