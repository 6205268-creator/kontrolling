import uuid

from sqlalchemy import TypeDecorator
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import CHAR


class Guid(TypeDecorator):
    """UUID type compatible with PostgreSQL (native UUID) and SQLite (CHAR(36))."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID as PG_UUID
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value) if isinstance(value, uuid.UUID) else value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value) if value else None


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass
