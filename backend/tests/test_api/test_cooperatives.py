import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, get_password_hash

# Import models from Clean Architecture modules
from app.modules.administration.infrastructure.models import AppUserModel as AppUser
from app.modules.cooperative_core.infrastructure.models import CooperativeModel as Cooperative


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
async def chairman_token(test_db) -> str:
    """Создаёт chairman пользователя с СТ и возвращает токен."""
    coop = Cooperative(name="СТ Председателя")
    test_db.add(coop)
    await test_db.flush()

    chairman = AppUser(
        username="chairman_user",
        email="chairman@example.com",
        hashed_password=get_password_hash("chairmanpass"),
        role="chairman",
        cooperative_id=coop.id,
        is_active=True,
    )
    test_db.add(chairman)
    await test_db.commit()

    return create_access_token(data={"sub": "chairman_user", "role": "chairman"})


@pytest.mark.asyncio
async def test_create_cooperative_by_admin(
    async_client: AsyncClient,
    admin_token: str,
) -> None:
    """Тест создания СТ от имени admin."""
    response = await async_client.post(
        "/api/cooperatives/",
        json={"name": "Новое СТ", "unp": "123456789"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Новое СТ"
    assert data["unp"] == "123456789"


@pytest.mark.asyncio
async def test_create_cooperative_by_treasurer_success(
    async_client: AsyncClient,
    treasurer_token: str,
) -> None:
    """Тест что любой авторизованный пользователь может создать СТ."""
    response = await async_client.post(
        "/api/cooperatives/",
        json={"name": "СТ Казначея 2"},
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_get_cooperatives_admin_sees_all(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
) -> None:
    """Тест что admin видит все СТ."""
    # Создаём несколько СТ
    for i in range(3):
        coop = Cooperative(name=f"СТ {i}")
        test_db.add(coop)
    await test_db.commit()

    response = await async_client.get(
        "/api/cooperatives/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3  # Как минимум 3 созданных


@pytest.mark.asyncio
async def test_get_cooperatives_treasurer_sees_only_own(
    async_client: AsyncClient,
    treasurer_token: str,
    test_db,
) -> None:
    """Тест что treasurer видит только своё СТ."""
    response = await async_client.get(
        "/api/cooperatives/",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "СТ Казначея"


@pytest.mark.asyncio
async def test_get_cooperative_by_id_admin(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
) -> None:
    """Тест получения СТ по ID для admin."""
    coop = Cooperative(name="СТ Для теста")
    test_db.add(coop)
    await test_db.commit()

    response = await async_client.get(
        f"/api/cooperatives/{coop.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "СТ Для теста"


@pytest.mark.asyncio
async def test_get_cooperative_by_id_treasurer_own(
    async_client: AsyncClient,
    treasurer_token: str,
    test_db,
) -> None:
    """Тест получения своего СТ по ID для treasurer."""
    # Получаем СТ казначея
    response = await async_client.get(
        "/api/cooperatives/",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )
    coop_id = response.json()[0]["id"]

    response = await async_client.get(
        f"/api/cooperatives/{coop_id}",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_cooperative_by_id_treasurer_foreign_forbidden(
    async_client: AsyncClient,
    treasurer_token: str,
    test_db,
) -> None:
    """Тест 403 при попытке treasurer получить чужое СТ."""
    # Создаём другое СТ
    other_coop = Cooperative(name="Чужое СТ")
    test_db.add(other_coop)
    await test_db.commit()

    response = await async_client.get(
        f"/api/cooperatives/{other_coop.id}",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_cooperative_by_admin(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
) -> None:
    """Тест обновления СТ от имени admin."""
    coop = Cooperative(name="СТ До обновления")
    test_db.add(coop)
    await test_db.commit()

    response = await async_client.patch(
        f"/api/cooperatives/{coop.id}",
        json={"name": "СТ После обновления"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "СТ После обновления"


@pytest.mark.asyncio
async def test_update_cooperative_by_treasurer_success(
    async_client: AsyncClient,
    treasurer_token: str,
    test_db,
) -> None:
    """Тест что любой авторизованный пользователь может обновить СТ."""
    coop = Cooperative(name="СТ Казначея")
    test_db.add(coop)
    await test_db.commit()

    response = await async_client.patch(
        f"/api/cooperatives/{coop.id}",
        json={"name": "Новое название"},
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_cooperative_by_admin(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
) -> None:
    """Тест удаления СТ от имени admin."""
    coop = Cooperative(name="СТ На удаление")
    test_db.add(coop)
    await test_db.commit()
    coop_id = coop.id

    response = await async_client.delete(
        f"/api/cooperatives/{coop_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 204

    # Проверяем что удалено
    response = await async_client.get(
        f"/api/cooperatives/{coop_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_cooperative_by_treasurer_success(
    async_client: AsyncClient,
    treasurer_token: str,
    test_db,
) -> None:
    """Тест что любой авторизованный пользователь может удалить СТ."""
    coop = Cooperative(name="СТ Казначея")
    test_db.add(coop)
    await test_db.commit()
    coop_id = coop.id

    response = await async_client.delete(
        f"/api/cooperatives/{coop_id}",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 204
