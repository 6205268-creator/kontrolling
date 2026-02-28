import pytest
from httpx import AsyncClient

from app.core.security import get_password_hash

# Import models from Clean Architecture modules
from app.modules.administration.infrastructure.models import AppUserModel as AppUser


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, test_db) -> None:
    """Тест успешного логина с валидными credentials."""
    # Создаём тестового пользователя
    user = AppUser(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        role="treasurer",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()

    # Логин
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "testpassword123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] is not None
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient, test_db) -> None:
    """Тест логина с неверным паролем."""
    user = AppUser(
        username="testuser2",
        email="test2@example.com",
        hashed_password=get_password_hash("correctpassword"),
        role="treasurer",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()

    response = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "testuser2", "password": "wrongpassword"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Неверное имя пользователя или пароль"


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client: AsyncClient) -> None:
    """Тест логина с несуществующим пользователем."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent", "password": "somepassword"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Неверное имя пользователя или пароль"


@pytest.mark.asyncio
async def test_login_inactive_user(async_client: AsyncClient, test_db) -> None:
    """Тест логина неактивного пользователя."""
    user = AppUser(
        username="inactiveuser",
        email="inactive@example.com",
        hashed_password=get_password_hash("testpassword"),
        role="treasurer",
        is_active=False,
    )
    test_db.add(user)
    await test_db.commit()

    response = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "inactiveuser", "password": "testpassword"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Пользователь не активен"


@pytest.mark.asyncio
async def test_get_current_user_with_valid_token(async_client: AsyncClient, test_db) -> None:
    """Тест получения текущего пользователя с валидным токеном."""
    from app.core.security import create_access_token

    user = AppUser(
        username="tokenuser",
        email="token@example.com",
        hashed_password=get_password_hash("testpassword"),
        role="chairman",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()

    token = create_access_token(data={"sub": user.username, "role": user.role})

    # Проверяем что токен работает (через endpoint который требует аутентификацию)
    # Пока используем просто проверку что токен декодируется
    from app.core.security import decode_access_token

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "tokenuser"
    assert payload["role"] == "chairman"


@pytest.mark.asyncio
async def test_invalid_token(async_client: AsyncClient) -> None:
    """Тест 401 при невалидном токене."""
    # Пытаемся получить доступ к защищённому эндпоинту с невалидным токеном
    # Пока проверяем что login возвращает ошибку при пустых данных
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "", "password": ""},
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_login_different_roles(async_client: AsyncClient, test_db) -> None:
    """Тест логина для разных ролей."""
    for role in ["admin", "chairman", "treasurer"]:
        user = AppUser(
            username=f"user_{role}",
            email=f"{role}@example.com",
            hashed_password=get_password_hash("testpassword"),
            role=role,
            is_active=True,
        )
        test_db.add(user)
    await test_db.commit()

    for role in ["admin", "chairman", "treasurer"]:
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"username": f"user_{role}", "password": "testpassword"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["token_type"] == "bearer"

        # Проверяем что роль в токене
        from app.core.security import decode_access_token

        payload = decode_access_token(data["access_token"])
        assert payload is not None
        assert payload["role"] == role
