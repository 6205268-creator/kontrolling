"""Загрузка пользователя для аутентификации (API-слой).

Используется из app.api.deps. Реализация в infrastructure — API не импортирует infrastructure.
"""

from app.modules.administration.infrastructure.user_loader import (
    get_user_by_email,
    get_user_by_identifier,
    get_user_by_username,
)

__all__ = ["get_user_by_identifier", "get_user_by_email", "get_user_by_username"]
