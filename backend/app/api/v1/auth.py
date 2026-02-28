from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token, verify_password
from app.models.app_user import AppUser
from app.schemas.auth import Token, UserLogin

router = APIRouter()


@router.post(
    "/login",
    response_model=Token,
    summary="Вход пользователя",
    description="Аутентификация пользователя по имени и паролю. Возвращает JWT токен для доступа к защищённым эндпоинтам.",
)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Аутентификация пользователя и получение JWT токена.

    - **username**: Имя пользователя
    - **password**: Пароль
    """
    from sqlalchemy import select

    result = await db.execute(select(AppUser).where(AppUser.username == login_data.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь не активен",
        )

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role,
            "username": user.username,
            "email": user.email,
            "cooperative_id": str(user.cooperative_id) if user.cooperative_id else None,
            "is_active": user.is_active,
        },
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=dict,
    summary="Информация о пользователе",
    description="Получение информации о текущем аутентифицированном пользователе (роль, email, СТ).",
)
async def get_me(current_user: AppUser = Depends(get_current_user)) -> dict:
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "cooperative_id": str(current_user.cooperative_id) if current_user.cooperative_id else None,
        "is_active": current_user.is_active,
    }
