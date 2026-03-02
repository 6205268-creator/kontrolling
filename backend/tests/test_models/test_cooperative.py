import uuid
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cooperative_core.infrastructure.models import CooperativeModel as Cooperative


@pytest.mark.asyncio
async def test_create_cooperative(test_db: AsyncSession) -> None:
    """Создание Cooperative с обязательными полями."""
    coop = Cooperative(name="СТ Ромашка", address="Минск, ул. Садовая 1")
    test_db.add(coop)
    await test_db.commit()
    await test_db.refresh(coop)
    assert coop.id is not None
    assert isinstance(coop.id, uuid.UUID)
    assert coop.name == "СТ Ромашка"
    assert coop.unp is None
    assert coop.address == "Минск, ул. Садовая 1"
    assert coop.created_at is not None
    assert coop.updated_at is not None


@pytest.mark.asyncio
async def test_cooperative_unp_unique(test_db: AsyncSession) -> None:
    """Уникальность UNP: второй Cooperative с тем же UNP не должен сохраниться."""
    from sqlalchemy.exc import IntegrityError

    coop1 = Cooperative(name="СТ Первое", unp="123456789")
    test_db.add(coop1)
    await test_db.commit()
    coop2 = Cooperative(name="СТ Второе", unp="123456789")
    test_db.add(coop2)
    with pytest.raises(IntegrityError):
        await test_db.commit()
    await test_db.rollback()


@pytest.mark.asyncio
async def test_cooperative_created_at_auto(test_db: AsyncSession) -> None:
    """Проверка автозаполнения created_at."""
    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.commit()
    await test_db.refresh(coop)
    assert coop.created_at is not None
    assert isinstance(coop.created_at, datetime)


@pytest.mark.asyncio
async def test_cooperative_via_fixture(sample_cooperative: Cooperative) -> None:
    """Фикстура sample_cooperative создаёт СТ с ожидаемыми полями."""
    assert sample_cooperative.id is not None
    assert sample_cooperative.name == "СТ Тестовый"
    assert sample_cooperative.unp == "999999999"
