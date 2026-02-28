import asyncio
import os
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Использовать SQLite для тестов, чтобы не требовать PostgreSQL/asyncpg при импорте app
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# Импортируем Base до app чтобы таблицы создались правильно
# Импорт моделей, чтобы таблицы попали в Base.metadata для create_all
import app.models  # noqa: F401
from app.db.base import Base

# Теперь импортируем app после установки DATABASE_URL
from app.main import app

# Регистрируем фикстуры из fixtures.py для использования во всех тестах
pytest_plugins = ["tests.fixtures"]


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
    """Создаёт AsyncClient для тестирования API, используя ту же БД что и test_db."""
    # Переопределяем зависимость get_db в приложении для использования test_db
    from app.api import deps
    from app.db import session as db_session

    # Переопределяем get_db чтобы использовалась test_db
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db

    app.dependency_overrides[deps.get_db] = override_get_db
    app.dependency_overrides[db_session.get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Очищаем overrides после теста
    app.dependency_overrides.clear()
