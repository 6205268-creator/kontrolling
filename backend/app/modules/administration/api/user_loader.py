"""Загрузка пользователя для аутентификации (API-слой).

Используется из app.api.deps; маппинг ORM → доменная сущность выполняется здесь,
чтобы слой Presentation (app.api) не зависел от Infrastructure.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.administration.domain.entities import AppUser


async def get_user_by_email(session: AsyncSession, email: str) -> AppUser | None:
    """Найти пользователя по email. Возвращает доменную сущность или None."""
    from app.modules.administration.infrastructure.models import AppUserModel

    result = await session.execute(select(AppUserModel).where(AppUserModel.email == email))
    model = result.scalar_one_or_none()
    if model is None:
        return None
    return model.to_domain()


async def get_user_by_identifier(session: AsyncSession, identifier: str) -> AppUser | None:
    """Найти пользователя по email или username (для обратной совместимости токенов).
    Сначала поиск по email, затем по username.
    """
    user = await get_user_by_email(session, identifier)
    if user is not None:
        return user
    return await get_user_by_username(session, identifier)


async def get_user_by_username(session: AsyncSession, username: str) -> AppUser | None:
    """Найти пользователя по username. Возвращает доменную сущность или None."""
    from app.modules.administration.infrastructure.models import AppUserModel

    result = await session.execute(select(AppUserModel).where(AppUserModel.username == username))
    model = result.scalar_one_or_none()
    if model is None:
        return None
    return model.to_domain()
