"""Загрузка пользователя для аутентификации (Infrastructure).

Используется из app.api.deps и из administration.api.user_loader.
Маппинг ORM → доменная сущность выполняется здесь.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.administration.domain.entities import AppUser

from .models import AppUserModel


async def get_user_by_email(session: AsyncSession, email: str) -> AppUser | None:
    """Найти пользователя по email. Возвращает доменную сущность или None."""
    result = await session.execute(select(AppUserModel).where(AppUserModel.email == email))
    model = result.scalar_one_or_none()
    if model is None:
        return None
    return model.to_domain()


async def get_user_by_username(session: AsyncSession, username: str) -> AppUser | None:
    """Найти пользователя по username. Возвращает доменную сущность или None."""
    result = await session.execute(select(AppUserModel).where(AppUserModel.username == username))
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
