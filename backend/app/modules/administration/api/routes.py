"""FastAPI routes for administration module (auth)."""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.config import settings
from app.core.security import create_access_token, verify_password
from app.modules.administration.api.user_loader import get_user_by_identifier
from app.modules.administration.domain.entities import AppUser

from .schemas import Token, UserInDB

router = APIRouter()


async def authenticate_user(db: AsyncSession, identifier: str, password: str) -> AppUser | None:
    """Authenticate user by email/username and password. Returns domain entity or None."""
    user = await get_user_by_identifier(db, identifier)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Вход в систему",
    description="Получить JWT токен для аутентификации.",
)
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """
    OAuth2 compatible token login.

    Get an access token for a user.
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
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
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.email,
            "cooperative_id": str(user.cooperative_id) if user.cooperative_id else None,
            "role": user.role,
        },
        expires_delta=access_token_expires,
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserInDB,
    summary="Текущий пользователь",
    description="Получить информацию о текущем пользователе.",
)
async def get_current_user_info(
    current_user: Annotated[AppUser, Depends(get_current_user)],
) -> UserInDB:
    """Get current user information."""
    return UserInDB(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        cooperative_id=current_user.cooperative_id,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )
