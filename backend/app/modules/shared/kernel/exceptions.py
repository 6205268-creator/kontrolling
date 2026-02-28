"""Domain exceptions.

Pure Python - no framework dependencies (FastAPI, SQLAlchemy, Pydantic).
"""


class DomainError(Exception):
    """Base exception for domain layer errors."""

    pass


class ValidationError(DomainError):
    """Exception for domain validation failures."""

    pass
