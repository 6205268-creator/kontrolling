"""Base entity classes for domain layer.

Pure Python - no framework dependencies (FastAPI, SQLAlchemy, Pydantic).
"""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class BaseEntity:
    """Base class for all domain entities.
    
    All entities should have a unique identifier.
    """

    id: UUID
