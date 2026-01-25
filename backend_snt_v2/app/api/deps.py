"""Dependencies: current user from X-User-Id header."""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.app_user import AppUser


def get_current_user(
    x_user_id: str | None = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> AppUser:
    """Load user from X-User-Id. If missing or invalid, return first admin."""
    if x_user_id:
        try:
            uid = int(x_user_id)
            u = db.execute(select(AppUser).where(AppUser.id == uid)).scalar_one_or_none()
            if u:
                return u
        except ValueError:
            pass
    admin = db.execute(select(AppUser).where(AppUser.role == "admin").limit(1)).scalar_one_or_none()
    if admin:
        return admin
    raise HTTPException(status_code=404, detail="No admin user found")
