import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, get_password_hash

# Import models from Clean Architecture modules
from app.modules.administration.infrastructure.models import AppUserModel as AppUser
from app.modules.cooperative_core.infrastructure.models import CooperativeModel as Cooperative
from app.modules.land_management.infrastructure.models import OwnerModel as Owner


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
async def owner_test_data(test_db) -> Owner:
    """Создаёт тестового владельца."""
    owner = Owner(
        owner_type="physical",
        name="Иванов Иван Иванович",
        tax_id="123456789",
        contact_phone="+375291234567",
        contact_email="ivanov@example.com",
    )
    test_db.add(owner)
    await test_db.commit()
    return owner


@pytest.mark.asyncio
async def test_create_owner_physical(
    async_client: AsyncClient,
    treasurer_token: str,
) -> None:
    """Тест создания владельца (физическое лицо) от имени treasurer."""
    response = await async_client.post(
        "/api/owners/",
        json={
            "owner_type": "physical",
            "name": "Петров Пётр Петрович",
            "tax_id": "987654321",
            "contact_phone": "+375299876543",
            "contact_email": "petrov@example.com",
        },
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Петров Пётр Петрович"
    assert data["tax_id"] == "987654321"
    assert data["owner_type"] == "physical"


@pytest.mark.asyncio
async def test_create_owner_legal(
    async_client: AsyncClient,
    admin_token: str,
) -> None:
    """Тест создания владельца (юридическое лицо) от имени admin."""
    response = await async_client.post(
        "/api/owners/",
        json={
            "owner_type": "legal",
            "name": "ООО Ромашка",
            "tax_id": "100200300",
            "contact_phone": "+375171234567",
            "contact_email": "info@romashka.by",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "ООО Ромашка"
    assert data["owner_type"] == "legal"


@pytest.mark.asyncio
async def test_create_owner_invalid_type(
    async_client: AsyncClient,
    treasurer_token: str,
) -> None:
    """Тест создания владельца с недопустимым owner_type."""
    response = await async_client.post(
        "/api/owners/",
        json={
            "owner_type": "invalid",
            "name": "Тест",
        },
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_owners_list(
    async_client: AsyncClient,
    test_db,
    treasurer_token: str,
) -> None:
    """Тест получения списка владельцев."""
    # Создаём несколько владельцев
    for i in range(3):
        owner = Owner(
            owner_type="physical",
            name=f"Владелец {i}",
            tax_id=f"tax{i}",
        )
        test_db.add(owner)
    await test_db.commit()

    response = await async_client.get(
        "/api/owners/",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


@pytest.mark.asyncio
async def test_get_owner_by_id(
    async_client: AsyncClient,
    owner_test_data: Owner,
    treasurer_token: str,
) -> None:
    """Тест получения владельца по ID."""
    response = await async_client.get(
        f"/api/owners/{owner_test_data.id}",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Иванов Иван Иванович"
    assert str(data["id"]) == str(owner_test_data.id)


@pytest.mark.asyncio
async def test_get_owner_not_found(
    async_client: AsyncClient,
    admin_token: str,
) -> None:
    """Тест получения несуществующего владельца."""
    import uuid

    fake_id = uuid.uuid4()

    response = await async_client.get(
        f"/api/owners/{fake_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_search_owners_by_name(
    async_client: AsyncClient,
    test_db,
    treasurer_token: str,
) -> None:
    """Тест поиска владельцев по имени."""
    owner1 = Owner(owner_type="physical", name="Иванов Иван", tax_id="111")
    owner2 = Owner(owner_type="physical", name="Петров Иван", tax_id="222")
    owner3 = Owner(owner_type="physical", name="Сидор Пётр", tax_id="333")
    test_db.add_all([owner1, owner2, owner3])
    await test_db.commit()

    response = await async_client.get(
        "/api/owners/search?q=Иван",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = [o["name"] for o in data]
    assert "Иванов Иван" in names
    assert "Петров Иван" in names


@pytest.mark.asyncio
async def test_search_owners_by_tax_id(
    async_client: AsyncClient,
    test_db,
    treasurer_token: str,
) -> None:
    """Тест поиска владельцев по tax_id."""
    owner1 = Owner(owner_type="physical", name="Тест 1", tax_id="123456")
    owner2 = Owner(owner_type="legal", name="ООО Тест", tax_id="654321")
    test_db.add_all([owner1, owner2])
    await test_db.commit()

    response = await async_client.get(
        "/api/owners/search?q=123",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["tax_id"] == "123456"


@pytest.mark.asyncio
async def test_update_owner(
    async_client: AsyncClient,
    owner_test_data: Owner,
    treasurer_token: str,
) -> None:
    """Тест обновления владельца."""
    response = await async_client.patch(
        f"/api/owners/{owner_test_data.id}",
        json={
            "name": "Иванов Иван Иванович (обновлено)",
            "contact_phone": "+375290000000",
        },
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Иванов Иван Иванович (обновлено)"
    assert data["contact_phone"] == "+375290000000"
    # Поля которые не обновлялись
    assert data["tax_id"] == "123456789"


@pytest.mark.asyncio
async def test_update_owner_not_found(
    async_client: AsyncClient,
    admin_token: str,
) -> None:
    """Тест обновления несуществующего владельца."""
    import uuid

    fake_id = uuid.uuid4()

    response = await async_client.patch(
        f"/api/owners/{fake_id}",
        json={"name": "Новое имя"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_owner_by_admin(
    async_client: AsyncClient,
    test_db,
    admin_token: str,
) -> None:
    """Тест удаления владельца от имени admin."""
    owner = Owner(owner_type="physical", name="На удаление", tax_id="000")
    test_db.add(owner)
    await test_db.commit()
    owner_id = owner.id

    response = await async_client.delete(
        f"/api/owners/{owner_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 204

    # Проверяем что удалено
    response = await async_client.get(
        f"/api/owners/{owner_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_owner_by_treasurer_success(
    async_client: AsyncClient,
    owner_test_data: Owner,
    treasurer_token: str,
) -> None:
    """Тест что любой авторизованный пользователь может удалить владельца."""
    response = await async_client.delete(
        f"/api/owners/{owner_test_data.id}",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_create_owner_without_required_fields(
    async_client: AsyncClient,
    admin_token: str,
) -> None:
    """Тест создания владельца без обязательных полей."""
    response = await async_client.post(
        "/api/owners/",
        json={"owner_type": "physical"},  # отсутствует name
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 422
