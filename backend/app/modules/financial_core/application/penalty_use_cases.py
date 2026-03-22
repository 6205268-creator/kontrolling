"""Use cases: расчёт и начисление пеней, списание пени-начисления."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.modules.accruals.application.dtos import AccrualCreate
from app.modules.accruals.application.use_cases import (
    ApplyAccrualUseCase,
    CancelAccrualUseCase,
    CreateAccrualUseCase,
)
from app.modules.accruals.domain.repositories import IAccrualRepository, IContributionTypeRepository
from app.modules.financial_core.domain.entities import DebtLine, PenaltySettings
from app.modules.financial_core.domain.penalty_strategy import PenaltyCalculator
from app.modules.financial_core.domain.repositories import (
    IDebtLineRepository,
    IPenaltySettingsRepository,
)
from app.modules.shared.kernel.exceptions import ValidationError


def pick_penalty_settings(
    rows: list[PenaltySettings],
    contribution_type_id: UUID,
    as_of: date,
) -> PenaltySettings | None:
    """Выбрать актуальную настройку: сначала по виду взноса, иначе общую (contribution_type_id is None)."""
    effective = [
        r
        for r in rows
        if r.effective_from <= as_of
        and (r.effective_to is None or r.effective_to >= as_of)
        and r.is_enabled
    ]
    if not effective:
        return None
    specific = [r for r in effective if r.contribution_type_id == contribution_type_id]
    pool = specific if specific else [r for r in effective if r.contribution_type_id is None]
    if not pool:
        return None
    return max(pool, key=lambda x: x.effective_from)


def penalty_operation_key(debt_line_id: UUID, as_of_date: date) -> str:
    """Уникальный номер операции для идемпотентного начисления пени (≤ 50 символов)."""
    return f"PEN{debt_line_id.hex[:8]}{as_of_date.strftime('%Y%m%d')}"


@dataclass(frozen=True)
class PenaltyCalcResult:
    debt_line_id: UUID
    financial_subject_id: UUID
    outstanding: Decimal
    overdue_days: int
    penalty_amount: Decimal
    contribution_type_id: UUID


class CalculatePenaltiesUseCase:
    """Предварительный расчёт пеней на дату (без записи в БД)."""

    def __init__(
        self,
        debt_line_repo: IDebtLineRepository,
        penalty_settings_repo: IPenaltySettingsRepository,
        calculator: PenaltyCalculator,
    ):
        self._debt_lines = debt_line_repo
        self._settings = penalty_settings_repo
        self._calculator = calculator

    def _overdue_days_for_display(
        self,
        debt_line: DebtLine,
        settings: PenaltySettings,
        as_of_date: date,
    ) -> int:
        if debt_line.due_date is None:
            return 0
        from datetime import timedelta

        penalty_start = debt_line.due_date + timedelta(days=settings.grace_period_days + 1)
        if as_of_date < penalty_start:
            return 0
        return (as_of_date - penalty_start).days + 1

    async def execute(self, cooperative_id: UUID, as_of_date: date) -> list[PenaltyCalcResult]:
        lines = await self._debt_lines.get_overdue(cooperative_id, as_of_date)
        settings_rows = await self._settings.list_for_cooperative(cooperative_id)
        out: list[PenaltyCalcResult] = []

        for line in lines:
            ps = pick_penalty_settings(settings_rows, line.contribution_type_id, as_of_date)
            if ps is None:
                continue
            penalty = self._calculator.calculate(line, ps, as_of_date)
            if penalty.is_zero:
                continue
            od_days = self._overdue_days_for_display(line, ps, as_of_date)
            out.append(
                PenaltyCalcResult(
                    debt_line_id=line.id,
                    financial_subject_id=line.financial_subject_id,
                    outstanding=line.outstanding_amount.amount,
                    overdue_days=od_days,
                    penalty_amount=penalty.amount,
                    contribution_type_id=line.contribution_type_id,
                )
            )
        return out


class AccruePenaltiesUseCase:
    """Создать начисления типа PENALTY по результатам расчёта (идемпотентно по operation_number)."""

    def __init__(
        self,
        debt_line_repo: IDebtLineRepository,
        penalty_settings_repo: IPenaltySettingsRepository,
        calculator: PenaltyCalculator,
        accrual_repo: IAccrualRepository,
        contribution_type_repo: IContributionTypeRepository,
        create_accrual: CreateAccrualUseCase,
        apply_accrual: ApplyAccrualUseCase,
    ):
        self._debt_lines = debt_line_repo
        self._settings = penalty_settings_repo
        self._calculate = CalculatePenaltiesUseCase(debt_line_repo, penalty_settings_repo, calculator)
        self._accrual_repo = accrual_repo
        self._contribution_types = contribution_type_repo
        self._create_accrual = create_accrual
        self._apply_accrual = apply_accrual

    async def execute(self, cooperative_id: UUID, as_of_date: date) -> list[UUID]:
        penalty_type = await self._contribution_types.get_by_code("PENALTY")
        if penalty_type is None:
            raise ValidationError("В справочнике нет системного вида взноса PENALTY")

        planned = await self._calculate.execute(cooperative_id, as_of_date)
        created_ids: list[UUID] = []

        for row in planned:
            op_key = penalty_operation_key(row.debt_line_id, as_of_date)
            existing = await self._accrual_repo.get_by_operation_number(op_key)
            if existing is not None:
                continue
            if row.penalty_amount <= Decimal("0"):
                continue

            data = AccrualCreate(
                financial_subject_id=row.financial_subject_id,
                contribution_type_id=penalty_type.id,
                amount=row.penalty_amount,
                accrual_date=as_of_date,
                period_start=as_of_date,
                period_end=as_of_date,
                due_date=as_of_date,
                operation_number=op_key,
            )
            accrual = await self._create_accrual.execute(data, cooperative_id)
            applied = await self._apply_accrual.execute(accrual.id, cooperative_id)
            created_ids.append(applied.id)

        return created_ids


class WriteOffPenaltyUseCase:
    """Списать начисление-пеню (отмена начисления с проверкой типа PENALTY)."""

    def __init__(
        self,
        accrual_repo: IAccrualRepository,
        contribution_type_repo: IContributionTypeRepository,
        cancel_accrual: CancelAccrualUseCase,
    ):
        self._accrual_repo = accrual_repo
        self._contribution_types = contribution_type_repo
        self._cancel = cancel_accrual

    async def execute(
        self,
        accrual_id: UUID,
        cooperative_id: UUID,
        user_id: UUID,
        reason: str | None = None,
    ) -> None:
        accrual = await self._accrual_repo.get_by_id(accrual_id, cooperative_id)
        if accrual is None:
            raise ValidationError("Начисление не найдено")
        ct = await self._contribution_types.get_by_id(accrual.contribution_type_id, UUID(int=0))
        if ct is None or ct.code != "PENALTY":
            raise ValidationError("Списание доступно только для начислений типа «Пени»")
        await self._cancel.execute(
            accrual_id,
            cooperative_id,
            cancelled_by_user_id=user_id,
            cancellation_reason=reason or "Списание пени",
        )
