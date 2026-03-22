"""Автопереход закрытого периода в locked после окна переоткрытия казначеем."""

from datetime import UTC, datetime

from app.modules.financial_core.domain.entities import FinancialPeriod


def ensure_aware_utc(dt: datetime) -> datetime:
    """Привести datetime к UTC aware (SQLite может вернуть naive)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def apply_auto_lock_if_window_expired(
    period: FinancialPeriod,
    period_reopen_allowed_days: int,
    now: datetime,
) -> bool:
    """Если период закрыт дольше, чем разрешено — перевести в locked.

    Returns:
        True, если сущность изменена (нужно сохранить в БД).
    """
    if period.status != "closed" or period.closed_at is None:
        return False
    closed_at = ensure_aware_utc(period.closed_at)
    now_utc = ensure_aware_utc(now) if now.tzinfo is None else now.astimezone(UTC)
    if (now_utc - closed_at).days > period_reopen_allowed_days:
        period.lock()
        return True
    return False
