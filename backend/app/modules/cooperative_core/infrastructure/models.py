"""Cooperative ORM model reference.

Uses the shared table definition from app.models to avoid duplicate
table registration in SQLAlchemy MetaData.
"""

from __future__ import annotations

from app.models.cooperative import Cooperative as CooperativeModel

__all__ = ["CooperativeModel"]
