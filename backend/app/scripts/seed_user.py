"""Создание первого пользователя для входа в систему.

Запуск из корня backend:
  python -m app.scripts.seed_user

Создаётся пользователь admin / admin (роль admin), если такого ещё нет.
Для продакшена смени пароль после первого входа.
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.session import async_session_maker
from app.modules.administration.infrastructure.models import AppUserModel


async def main() -> int:
    async with async_session_maker() as session:
        result = await session.execute(select(AppUserModel).where(AppUserModel.username == "admin"))
        if result.scalar_one_or_none() is not None:
            print(
                "Пользователь admin уже существует. Вход: admin / <пароль, заданный при создании>"
            )
            return 0

        user = AppUserModel(
            username="admin",
            email="admin@controlling.local",
            hashed_password=get_password_hash("admin"),
            role="admin",
            cooperative_id=None,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        print("Создан пользователь: username=admin, password=admin")
        print("Войди в приложение и смени пароль в продакшене.")
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
