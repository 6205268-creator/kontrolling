"""Cooperative domain entities.

Pure Python - no framework dependencies (FastAPI, SQLAlchemy, Pydantic).
"""

from dataclasses import dataclass
from datetime import datetime

from app.modules.shared.kernel.entities import BaseEntity


@dataclass
class Cooperative(BaseEntity):
    """Садоводческое товарищество (СТ).

    Основная организация-владелец земельных участков.
    Каждое СТ независимо и имеет своих владельцев, участки, финансы.
    """

    name: str
    unp: str | None = None
    address: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
