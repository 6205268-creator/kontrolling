from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки backend v2 (физ. лица, члены СНТ, участки)."""

    DATABASE_URL: str = "sqlite:///./snt_v2.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
