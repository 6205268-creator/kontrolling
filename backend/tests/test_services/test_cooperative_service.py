import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.cooperative import CooperativeCreate, CooperativeUpdate
from app.services.cooperative_service import (
    create_cooperative,
    delete_cooperative,
    get_cooperative,
    get_cooperatives,
    update_cooperative,
)


@pytest.mark.asyncio
async def test_create_cooperative(test_db: AsyncSession) -> None:
    """Тест создания Cooperative."""
    data = CooperativeCreate(
        name="СТ Ромашка",
        unp="123456789",
        address="г. Минск, ул. Примерная, 1",
    )
    cooperative = await create_cooperative(test_db, data)

    assert cooperative.name == "СТ Ромашка"
    assert cooperative.unp == "123456789"
    assert cooperative.address == "г. Минск, ул. Примерная, 1"
    assert cooperative.id is not None


@pytest.mark.asyncio
async def test_get_cooperative(test_db: AsyncSession) -> None:
    """Тест получения Cooperative по ID."""
    data = CooperativeCreate(name="СТ Тест")
    cooperative = await create_cooperative(test_db, data)

    result = await get_cooperative(test_db, cooperative.id)
    assert result is not None
    assert result.id == cooperative.id
    assert result.name == "СТ Тест"


@pytest.mark.asyncio
async def test_get_cooperative_not_found(test_db: AsyncSession) -> None:
    """Тест получения несуществующего Cooperative."""
    import uuid

    result = await get_cooperative(test_db, uuid.uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_cooperatives_list(test_db: AsyncSession) -> None:
    """Тест получения списка Cooperative."""
    for i in range(3):
        data = CooperativeCreate(name=f"СТ {i}")
        await create_cooperative(test_db, data)

    cooperatives = await get_cooperatives(test_db, skip=0, limit=10)
    assert len(cooperatives) == 3


@pytest.mark.asyncio
async def test_get_cooperatives_pagination(test_db: AsyncSession) -> None:
    """Тест пагинации списка Cooperative."""
    for i in range(5):
        data = CooperativeCreate(name=f"СТ {i}")
        await create_cooperative(test_db, data)

    cooperatives = await get_cooperatives(test_db, skip=2, limit=2)
    assert len(cooperatives) == 2


@pytest.mark.asyncio
async def test_get_cooperatives_by_id(test_db: AsyncSession) -> None:
    """Тест получения одного Cooperative по ID через get_cooperatives."""
    data = CooperativeCreate(name="СТ Один")
    cooperative = await create_cooperative(test_db, data)

    cooperatives = await get_cooperatives(test_db, cooperative_id=cooperative.id)
    assert len(cooperatives) == 1
    assert cooperatives[0].id == cooperative.id


@pytest.mark.asyncio
async def test_update_cooperative(test_db: AsyncSession) -> None:
    """Тест обновления Cooperative."""
    data = CooperativeCreate(name="СТ До")
    cooperative = await create_cooperative(test_db, data)

    update_data = CooperativeUpdate(name="СТ После", address="Новый адрес")
    updated = await update_cooperative(test_db, cooperative.id, update_data)

    assert updated is not None
    assert updated.name == "СТ После"
    assert updated.address == "Новый адрес"
    assert updated.id == cooperative.id


@pytest.mark.asyncio
async def test_update_cooperative_not_found(test_db: AsyncSession) -> None:
    """Тест обновления несуществующего Cooperative."""
    import uuid

    update_data = CooperativeUpdate(name="Новое имя")
    result = await update_cooperative(test_db, uuid.uuid4(), update_data)
    assert result is None


@pytest.mark.asyncio
async def test_update_cooperative_partial(test_db: AsyncSession) -> None:
    """Тест частичного обновления Cooperative."""
    data = CooperativeCreate(name="СТ Тест", unp="123", address="Адрес")
    cooperative = await create_cooperative(test_db, data)

    update_data = CooperativeUpdate(name="Обновлённое СТ")
    updated = await update_cooperative(test_db, cooperative.id, update_data)

    assert updated is not None
    assert updated.name == "Обновлённое СТ"
    assert updated.unp == "123"  # Не изменилось
    assert updated.address == "Адрес"  # Не изменилось


@pytest.mark.asyncio
async def test_delete_cooperative(test_db: AsyncSession) -> None:
    """Тест удаления Cooperative."""
    data = CooperativeCreate(name="СТ На удаление")
    cooperative = await create_cooperative(test_db, data)

    result = await delete_cooperative(test_db, cooperative.id)
    assert result is True

    deleted = await get_cooperative(test_db, cooperative.id)
    assert deleted is None


@pytest.mark.asyncio
async def test_delete_cooperative_not_found(test_db: AsyncSession) -> None:
    """Тест удаления несуществующего Cooperative."""
    import uuid

    result = await delete_cooperative(test_db, uuid.uuid4())
    assert result is False
