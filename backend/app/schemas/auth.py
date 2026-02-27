from pydantic import BaseModel, Field


class Token(BaseModel):
    """Схема JWT токена."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Данные из JWT токена."""

    username: str | None = None
    role: str | None = None


class UserLogin(BaseModel):
    """Схема для входа пользователя."""

    username: str = Field(..., description="Имя пользователя", min_length=1, max_length=50)
    password: str = Field(..., description="Пароль", min_length=1)
