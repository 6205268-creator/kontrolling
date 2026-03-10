"""Mapping between Cooperative ORM model and domain entity."""

from __future__ import annotations

from app.modules.cooperative_core.domain.entities import Cooperative
from app.modules.cooperative_core.infrastructure.models import CooperativeModel as CooperativeORM


def orm_to_domain(orm: CooperativeORM) -> Cooperative:
    """Convert SQLAlchemy Cooperative model to domain entity."""
    return Cooperative(
        id=orm.id,
        name=orm.name,
        unp=orm.unp,
        address=orm.address,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


def domain_to_orm(entity: Cooperative) -> CooperativeORM:
    """Create SQLAlchemy Cooperative model from domain entity."""
    return CooperativeORM(
        id=entity.id,
        name=entity.name,
        unp=entity.unp,
        address=entity.address,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
