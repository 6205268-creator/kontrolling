from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings


settings = Settings()

engine = create_engine(settings.DATABASE_URL, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    """Зависимость FastAPI для получения сессии БД."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

