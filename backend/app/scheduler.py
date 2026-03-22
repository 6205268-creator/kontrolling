"""Фоновые задачи (APScheduler): автоначисление пеней по расписанию СТ."""

import logging
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.modules.shared.kernel.exceptions import ValidationError

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _penalty_accrual_tick() -> None:
    from app.db.session import async_session_maker
    from app.modules.accruals.application.use_cases import ApplyAccrualUseCase, CreateAccrualUseCase
    from app.modules.accruals.infrastructure.repositories import (
        AccrualRepository,
        ContributionTypeRepository,
    )
    from app.modules.cooperative_core.infrastructure.repositories import CooperativeRepository
    from app.modules.financial_core.application.penalty_use_cases import AccruePenaltiesUseCase
    from app.modules.financial_core.application.period_operation_guard import PeriodOperationGuard
    from app.modules.financial_core.domain.penalty_strategy import (
        PenaltyCalculator,
        SimpleDailyPenaltyStrategy,
    )
    from app.modules.financial_core.infrastructure.repositories import (
        DebtLineRepository,
        FinancialPeriodRepository,
        FinancialSubjectRepository,
        PenaltySettingsRepository,
    )
    from app.modules.shared.kernel.events import EventDispatcher

    today = date.today()
    async with async_session_maker() as session:
        coop_repo = CooperativeRepository(session)
        coops = await coop_repo.get_all_for_admin()
        period_repo = FinancialPeriodRepository(session)
        period_guard = PeriodOperationGuard(period_repo, coop_repo)
        strategy = SimpleDailyPenaltyStrategy()
        calculator = PenaltyCalculator(strategy)

        for coop in coops:
            sched = coop.penalty_accrual_schedule
            if sched == "disabled":
                continue
            if sched == "monthly" and today.day != 1:
                continue
            if sched == "weekly" and today.weekday() != 0:
                continue

            debt_repo = DebtLineRepository(session)
            penalty_settings_repo = PenaltySettingsRepository(session)
            accrual_repo = AccrualRepository(session)
            contribution_type_repo = ContributionTypeRepository(session)
            fs_repo = FinancialSubjectRepository(session)
            create_uc = CreateAccrualUseCase(accrual_repo, fs_repo, period_guard)
            apply_uc = ApplyAccrualUseCase(
                accrual_repo, EventDispatcher(), period_guard, fs_repo
            )
            uc = AccruePenaltiesUseCase(
                debt_repo,
                penalty_settings_repo,
                calculator,
                accrual_repo,
                contribution_type_repo,
                create_uc,
                apply_uc,
            )
            try:
                created = await uc.execute(coop.id, today)
                if created:
                    logger.info(
                        "Penalty accrual job: cooperative=%s created %d accruals",
                        coop.id,
                        len(created),
                    )
            except ValidationError as exc:
                logger.warning(
                    "Penalty accrual skipped for cooperative %s: %s "
                    "(likely closed period — reopen period or change accrual date)",
                    coop.id,
                    exc,
                )
            except Exception:
                logger.exception("Penalty accrual failed for cooperative %s", coop.id)


def start_penalty_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(_penalty_accrual_tick, "cron", hour=3, minute=0, id="penalty_accrual_daily")
    _scheduler.start()
    logger.info("Penalty scheduler started (daily 03:00)")


def shutdown_penalty_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Penalty scheduler stopped")
