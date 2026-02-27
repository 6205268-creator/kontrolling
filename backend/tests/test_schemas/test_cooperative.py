from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.cooperative import CooperativeCreate, CooperativeInDB, CooperativeUpdate


def test_cooperative_create_valid() -> None:
    """Валидация CooperativeCreate с корректными данными."""
    data = {
        "name": "СТ Ромашка",
        "unp": "123456789",
        "address": "г. Минск, ул. Примерная, 1",
    }
    schema = CooperativeCreate(**data)

    assert schema.name == "СТ Ромашка"
    assert schema.unp == "123456789"
    assert schema.address == "г. Минск, ул. Примерная, 1"


def test_cooperative_create_minimal() -> None:
    """Валидация CooperativeCreate с минимальными данными."""
    data = {"name": "СТ Минимальное"}
    schema = CooperativeCreate(**data)

    assert schema.name == "СТ Минимальное"
    assert schema.unp is None
    assert schema.address is None


def test_cooperative_create_name_required() -> None:
    """Проверка что name обязательное поле."""
    with pytest.raises(ValidationError) as exc_info:
        CooperativeCreate()
    assert "name" in str(exc_info.value)


def test_cooperative_create_name_max_length() -> None:
    """Проверка максимальной длины name."""
    long_name = "A" * 300
    with pytest.raises(ValidationError):
        CooperativeCreate(name=long_name)


def test_cooperative_update_partial() -> None:
    """Валидация CooperativeUpdate с частичными данными."""
    data = {"name": "Новое название"}
    schema = CooperativeUpdate(**data)

    assert schema.name == "Новое название"
    assert schema.unp is None
    assert schema.address is None


def test_cooperative_update_empty() -> None:
    """Валидация CooperativeUpdate с пустыми данными."""
    schema = CooperativeUpdate()
    assert schema.name is None
    assert schema.unp is None
    assert schema.address is None


def test_cooperative_in_db_from_model() -> None:
    """Сериализация SQLAlchemy модели в CooperativeInDB."""
    # Создаём mock-объект (имитируем модель из БД)
    class MockCooperative:
        id = uuid4()
        name = "СТ Тест"
        unp = "987654321"
        address = "г. Гомель, ул. Тестовая, 10"
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)

    mock = MockCooperative()
    schema = CooperativeInDB.model_validate(mock)

    assert schema.id == mock.id
    assert schema.name == "СТ Тест"
    assert schema.unp == "987654321"
    assert schema.address == "г. Гомель, ул. Тестовая, 10"
    assert isinstance(schema.created_at, datetime)
    assert isinstance(schema.updated_at, datetime)


def test_cooperative_in_db_config() -> None:
    """Проверка что model_config настроен для from_attributes."""
    assert CooperativeInDB.model_config["from_attributes"] is True
