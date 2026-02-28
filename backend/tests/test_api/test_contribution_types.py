import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, get_password_hash
from app.models.app_user import AppUser
from app.models.contribution_type import ContributionType
from app.models.cooperative import Cooperative


@pytest.fixture
async def auth_token(test_db) -> str:
    """Токен любого авторизованного пользователя."""
    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()
    user = AppUser(
        username="user_ct",
        email="ct@example.com",
        hashed_password=get_password_hash("pass"),
        role="treasurer",
        cooperative_id=coop.id,
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    return create_access_token(data={"sub": "user_ct", "role": "treasurer"})


@pytest.fixture
async def contribution_type_records(test_db) -> list[ContributionType]:
    """Несколько видов взносов."""
    types_list = [
        ContributionType(name="Членский", code="MEMBER", description="Членский взнос"),
        ContributionType(name="Целевой", code="TARGET", description=None),
    ]
    for t in types_list:
        test_db.add(t)
    await test_db.commit()
    return types_list


@pytest.mark.asyncio
async def test_get_contribution_types_returns_list(
    async_client: AsyncClient,
    auth_token: str,
    contribution_type_records: list[ContributionType],
) -> None:
    """GET /api/v1/contribution-types/ возвращает список видов взносов."""
    response = await async_client.get(
        "/api/v1/contribution-types/",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    names = [item["name"] for item in data]
    assert "Членский" in names
    assert "Целевой" in names
    for item in data:
        assert "id" in item
        assert "name" in item
        assert "code" in item


@pytest.mark.asyncio
async def test_get_contribution_types_requires_auth(async_client: AsyncClient) -> None:
    """GET /api/v1/contribution-types/ без токена возвращает 401."""
    response = await async_client.get("/api/v1/contribution-types/")
    assert response.status_code == 401
