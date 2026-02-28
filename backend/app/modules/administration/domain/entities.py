"""Administration domain entities."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.shared.kernel.entities import BaseEntity


@dataclass
class AppUser(BaseEntity):
    """Пользователь системы."""
    username: str
    email: str
    hashed_password: str
    full_name: str | None = None
    role: str = "user"  # admin, chairman, treasurer
    cooperative_id: UUID | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
