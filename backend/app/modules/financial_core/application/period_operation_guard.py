"""Проверка, что операция допустима в открытом финансовом периоде."""

from datetime import UTC, date, datetime
from uuid import UUID

from app.modules.cooperative_core.domain.repositories import ICooperativeRepository
from app.modules.financial_core.application.period_auto_lock import (
    apply_auto_lock_if_window_expired,
)
from app.modules.financial_core.domain.repositories import IFinancialPeriodRepository
from app.modules.shared.kernel.exceptions import ValidationError


class PeriodOperationGuard:
    """Блокирует создание/отмену операций в закрытом или заблокированном периоде."""

    def __init__(
        self,
        period_repo: IFinancialPeriodRepository,
        coop_repo: ICooperativeRepository,
    ):
        self._period_repo = period_repo
        self._coop_repo = coop_repo

    async def ensure_open_for_date(self, cooperative_id: UUID, event_date: date) -> None:
        """Если на дату есть финпериод и он не open — ValidationError."""
        period = await self._period_repo.get_by_date(cooperative_id, event_date)
        if period is None:
            return

        coop = await self._coop_repo.get_by_id(cooperative_id, cooperative_id)
        allowed_days = coop.period_reopen_allowed_days if coop else 30
        now = datetime.now(UTC)
        if apply_auto_lock_if_window_expired(period, allowed_days, now):
            await self._period_repo.update(period)

        if period.status != "open":
            raise ValidationError(
                f"Финансовый период за эту дату недоступен для операций (статус: {period.status})"
            )
