import asyncio
import os
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Использовать SQLite для тестов, чтобы не требовать PostgreSQL/asyncpg при импорте app
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-tests-only-32chars")

# Импортируем Base до app чтобы таблицы создались правильно
# Импорт моделей из модулей Clean Architecture
import app.modules.accruals.infrastructure.models  # noqa: F401
import app.modules.administration.infrastructure.models  # noqa: F401
import app.modules.cooperative_core.infrastructure.models  # noqa: F401
import app.modules.expenses.infrastructure.models  # noqa: F401
import app.modules.financial_core.infrastructure.models  # noqa: F401
import app.modules.land_management.infrastructure.models  # noqa: F401
import app.modules.meters.infrastructure.models  # noqa: F401
import app.modules.payments.infrastructure.models  # noqa: F401
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
    """Одна in-memory SQLite на тест: и HTTP-запросы (get_db), и обработчики событий.

    Иначе async_session_maker приложения пишет в другой :memory:, чем сессия из override_get_db,
    и DebtLine / распределение платежей не видны в API-тестах.
    """
    from app.db import session as db_sess
    from app.modules.financial_core.infrastructure.event_handlers import setup_event_handlers
    from app.modules.financial_core.infrastructure.repositories import (
        DebtLineRepository,
        FinancialSubjectRepository,
    )
    from app.modules.payment_distribution.infrastructure.event_handlers import (
        setup_payment_distribution_handlers,
    )
    from app.modules.shared.kernel.events import EventDispatcher

    pool_kw = {}
    connect_kw = {}
    if "sqlite" in TEST_DATABASE_URL:
        connect_kw["check_same_thread"] = False
        # Одно соединение на все async-сессии — иначе :memory: и event handlers видят разные БД
        pool_kw["poolclass"] = StaticPool

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args=connect_kw,
        **pool_kw,
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

    prev_engine = db_sess.engine
    if prev_engine is not engine:
        await prev_engine.dispose()
    db_sess.engine = engine
    db_sess.async_session_maker = async_session

    EventDispatcher.clear()
    setup_event_handlers(
        EventDispatcher(),
        async_session,
        FinancialSubjectRepository,
        DebtLineRepository,
    )
    setup_payment_distribution_handlers(EventDispatcher(), async_session)

    async with async_session() as session:
        yield session

    # create_task в обработчиках событий — дать задачам завершиться до dispose пула
    await asyncio.sleep(0.35)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Создаёт AsyncClient для тестирования API, используя ту же БД что и test_db."""
    # Переопределяем зависимость get_db в приложении для использования test_db
    from app.api import deps
    from app.db import session as db_session

    # Как app.db.session.get_db: commit после успешного запроса (репозитории только flush).
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        try:
            yield test_db
            await test_db.commit()
        except Exception:
            await test_db.rollback()
            raise

    app.dependency_overrides[deps.get_db] = override_get_db
    app.dependency_overrides[db_session.get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Очищаем overrides после теста
    app.dependency_overrides.clear()
