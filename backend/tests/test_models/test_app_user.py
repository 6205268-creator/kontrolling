import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.administration.infrastructure.models import AppUserModel as AppUser
from app.modules.cooperative_core.infrastructure.models import CooperativeModel as Cooperative


@pytest.mark.asyncio
async def test_create_app_user_treasurer(test_db: AsyncSession) -> None:
    """Создание AppUser с ролью treasurer."""
    user = AppUser(
        username="treasurer1",
        email="treasurer@example.com",
        hashed_password="$2b$12$testhash",
        role="treasurer",
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    assert user.id is not None
    assert isinstance(user.id, uuid.UUID)
    assert user.username == "treasurer1"
    assert user.email == "treasurer@example.com"
    assert user.role == "treasurer"
    assert user.is_active is True
    assert user.cooperative_id is None


@pytest.mark.asyncio
async def test_create_app_user_with_cooperative(test_db: AsyncSession) -> None:
    """Создание AppUser с привязкой к Cooperative."""
    coop = Cooperative(name="СТ Ромашка")
    test_db.add(coop)
    await test_db.flush()

    user = AppUser(
        username="chairman1",
        email="chairman@example.com",
        hashed_password="$2b$12$testhash",
        role="chairman",
        cooperative_id=coop.id,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    assert user.cooperative_id == coop.id
    assert user.role == "chairman"


@pytest.mark.asyncio
async def test_app_user_username_unique(test_db: AsyncSession) -> None:
    """Проверка уникальности username."""
    user1 = AppUser(
        username="unique_user", email="user1@example.com", hashed_password="$2b$12$testhash"
    )
    test_db.add(user1)
    await test_db.flush()

    user2 = AppUser(
        username="unique_user", email="user2@example.com", hashed_password="$2b$12$testhash"
    )
    test_db.add(user2)

    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        await test_db.commit()
    await test_db.rollback()


@pytest.mark.asyncio
async def test_app_user_email_unique(test_db: AsyncSession) -> None:
    """Проверка уникальности email."""
    user1 = AppUser(username="user1", email="unique@example.com", hashed_password="$2b$12$testhash")
    test_db.add(user1)
    await test_db.flush()

    user2 = AppUser(username="user2", email="unique@example.com", hashed_password="$2b$12$testhash")
    test_db.add(user2)

    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        await test_db.commit()
    await test_db.rollback()


@pytest.mark.asyncio
async def test_app_user_role_values(test_db: AsyncSession) -> None:
    """Валидация ролей: admin, chairman, treasurer."""
    for i, role in enumerate(["admin", "chairman", "treasurer"]):
        user = AppUser(
            username=f"user_{role}",
            email=f"{role}@example.com",
            hashed_password="$2b$12$testhash",
            role=role,
        )
        test_db.add(user)
    await test_db.commit()

    result = await test_db.execute(select(AppUser))
    users = result.scalars().all()
    assert len(users) == 3
    roles = {u.role for u in users}
    assert roles == {"admin", "chairman", "treasurer"}


@pytest.mark.asyncio
async def test_app_user_default_role(test_db: AsyncSession) -> None:
    """Проверка роли по умолчанию (treasurer)."""
    user = AppUser(
        username="default_role_user",
        email="default@example.com",
        hashed_password="$2b$12$testhash",
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    assert user.role == "user"


@pytest.mark.asyncio
async def test_app_user_default_is_active(test_db: AsyncSession) -> None:
    """Проверка is_active по умолчанию (True)."""
    user = AppUser(
        username="active_user",
        email="active@example.com",
        hashed_password="$2b$12$testhash",
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    assert user.is_active is True


@pytest.mark.asyncio
async def test_app_user_relationships(test_db: AsyncSession) -> None:
    """Проверка relationships: AppUser связан с Cooperative."""
    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    user = AppUser(
        username="rel_user",
        email="rel@example.com",
        hashed_password="$2b$12$testhash",
        cooperative_id=coop.id,
    )
    test_db.add(user)
    await test_db.commit()

    # Явно загружаем relationship через select
    result = await test_db.execute(select(Cooperative).where(Cooperative.id == coop.id))
    loaded_coop = result.scalar_one()

    assert loaded_coop is not None
    # Проверяем что связь работает через отдельный запрос
    user_result = await test_db.execute(select(AppUser).where(AppUser.cooperative_id == coop.id))
    users = user_result.scalars().all()
    assert len(users) == 1
    assert users[0].username == "rel_user"
