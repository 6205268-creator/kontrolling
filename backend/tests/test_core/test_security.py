from datetime import datetime, timedelta, timezone

from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


def test_get_password_hash() -> None:
    """Тест хеширования пароля."""
    password = "test123"
    hashed = get_password_hash(password)

    assert hashed != password
    assert hashed.startswith("$2")  # bcrypt формат


def test_verify_password_correct() -> None:
    """Тест верификации правильного пароля."""
    password = "test123"
    hashed = get_password_hash(password)

    assert verify_password(password, hashed) is True


def test_verify_password_incorrect() -> None:
    """Тест верификации неправильного пароля."""
    password = "test123"
    wrong_password = "wrong_password"
    hashed = get_password_hash(password)

    assert verify_password(wrong_password, hashed) is False


def test_create_access_token() -> None:
    """Тест создания JWT токена."""
    data = {"sub": "testuser", "role": "treasurer"}
    token = create_access_token(data)

    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_with_custom_expiry() -> None:
    """Тест создания токена с кастомным временем жизни."""
    data = {"sub": "testuser"}
    expires_delta = timedelta(hours=2)
    token = create_access_token(data, expires_delta=expires_delta)

    assert isinstance(token, str)


def test_decode_access_token() -> None:
    """Тест декодирования JWT токена."""
    data = {"sub": "testuser", "role": "treasurer"}
    token = create_access_token(data)
    payload = decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == "testuser"
    assert payload["role"] == "treasurer"
    assert "exp" in payload


def test_decode_invalid_token() -> None:
    """Тест декодирования невалидного токена."""
    invalid_token = "invalid.token.here"
    payload = decode_access_token(invalid_token)

    assert payload is None


def test_decode_expired_token() -> None:
    """Тест декодирования истёкшего токена."""
    data = {"sub": "testuser"}
    expires_delta = timedelta(seconds=-1)  # Уже истёк
    token = create_access_token(data, expires_delta=expires_delta)
    payload = decode_access_token(token)

    assert payload is None


def test_token_contains_expiration() -> None:
    """Тест наличия срока действия в токене."""
    data = {"sub": "testuser"}
    token = create_access_token(data)
    payload = decode_access_token(token)

    assert payload is not None
    exp_timestamp = payload["exp"]
    exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
    now = datetime.now(timezone.utc)

    # Токен должен действовать примерно 30 минут (default ACCESS_TOKEN_EXPIRE_MINUTES)
    assert exp_datetime > now
    assert exp_datetime < now + timedelta(minutes=31)
