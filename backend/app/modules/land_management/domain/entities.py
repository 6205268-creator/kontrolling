"""Land Management domain entities.

Pure Python - no framework dependencies (FastAPI, SQLAlchemy, Pydantic).
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.modules.shared.kernel.entities import BaseEntity


@dataclass
class Owner(BaseEntity):
    """Владелец (физическое или юридическое лицо).

    Может владеть земельными участками (через PlotOwnership),
    приборами учёта (Meter), а также совершать платежи.
    """

    owner_type: str  # "physical" or "legal"
    name: str
    tax_id: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class LandPlot(BaseEntity):
    """Земельный участок в садоводческом товариществе.

    Каждый участок принадлежит одному СТ и может иметь нескольких владельцев
    (через таблицу PlotOwnership). На участке могут располагаться приборы учёта.
    """

    cooperative_id: UUID
    plot_number: str
    area_sqm: Decimal
    cadastral_number: str | None = None
    status: str = "active"  # "active", "vacant", "archived"
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class PlotOwnership(BaseEntity):
    """Право собственности на земельный участок.

    Связывает владельца (Owner) с участком (LandPlot) на определённый период.
    Поддерживает долевую собственность (например, 1/2, 1/3).
    is_primary=True означает, что владелец является членом СТ.
    """

    land_plot_id: UUID
    owner_id: UUID
    share_numerator: int
    share_denominator: int
    is_primary: bool = False
    valid_from: date | None = None
    valid_to: date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
