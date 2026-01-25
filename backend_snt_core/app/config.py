from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения ядра учёта СНТ."""

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/snt_core"

    class Config:
        env_file = "backend_snt_core/.env"
        env_file_encoding = "utf-8"

