from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.modules.administration.domain.entities import AppUser
from app.modules.administration.api.user_loader import get_user_by_identifier

__all__ = ["get_db", "get_current_user", "require_role", "oauth2_scheme"]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
) -> AppUser:
    """Получение текущего пользователя из JWT токена."""
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или истёкший токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: str | None = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен: отсутствует username",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user_by_identifier(db, username)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден или не активен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_role(allowed_roles: list[str]):
    """Проверка роли пользователя (factory для Depends)."""

    async def dependency(current_user: Annotated[AppUser, Depends(get_current_user)]) -> AppUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Требуется одна из ролей: {', '.join(allowed_roles)}",
            )
        return current_user

    return dependency
