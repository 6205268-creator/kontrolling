"""API: расчёт и начисление пеней, настройки, списание пени-начисления."""

from datetime import UTC, date, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.modules.administration.domain.entities import AppUser
from app.modules.deps import (
    get_accrue_penalties_use_case,
    get_calculate_penalties_use_case,
    get_penalty_settings_repository,
    get_write_off_penalty_use_case,
)
from app.modules.financial_core.domain.entities import PenaltySettings
from app.modules.shared.kernel.exceptions import ValidationError

from .penalties_schemas import (
    PenaltyCalcRowOut,
    PenaltySettingsCreate,
    PenaltySettingsOut,
    PenaltySettingsUpdate,
    WriteOffPenaltyBody,
)

router = APIRouter()


def _financial_roles(user: AppUser) -> None:
    if user.role not in ("admin", "treasurer", "chairman"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав",
        )


def _coop(user: AppUser, cooperative_id: UUID) -> UUID:
    if user.role == "admin":
        return cooperative_id
    if user.cooperative_id != cooperative_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к СТ")
    return cooperative_id


@router.get(
    "/calculate",
    response_model=list[PenaltyCalcRowOut],
    summary="Расчёт пеней без записи",
)
async def calculate_penalties(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_calculate_penalties_use_case),
    cooperative_id: UUID = Query(...),
    as_of_date: date | None = Query(None),
) -> list[PenaltyCalcRowOut]:
    _financial_roles(current_user)
    cid = _coop(current_user, cooperative_id)
    ref = as_of_date or date.today()
    rows = await use_case.execute(cid, ref)
    return [
        PenaltyCalcRowOut(
            debt_line_id=r.debt_line_id,
            financial_subject_id=r.financial_subject_id,
            outstanding=r.outstanding,
            overdue_days=r.overdue_days,
            penalty_amount=r.penalty_amount,
            contribution_type_id=r.contribution_type_id,
        )
        for r in rows
    ]


@router.post(
    "/accrue",
    response_model=list[UUID],
    summary="Зафиксировать пени (начисления PENALTY)",
)
async def accrue_penalties(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_accrue_penalties_use_case),
    cooperative_id: UUID = Query(...),
    as_of_date: date | None = Query(None),
) -> list[UUID]:
    _financial_roles(current_user)
    cid = _coop(current_user, cooperative_id)
    ref = as_of_date or date.today()
    try:
        return await use_case.execute(cid, ref)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post(
    "/{accrual_id}/write-off",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Списать начисление-пеню",
)
async def write_off_penalty(
    accrual_id: UUID,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_write_off_penalty_use_case),
    cooperative_id: UUID = Query(...),
    body: WriteOffPenaltyBody | None = None,
) -> None:
    _financial_roles(current_user)
    cid = _coop(current_user, cooperative_id)
    try:
        await use_case.execute(
            accrual_id,
            cid,
            current_user.id,
            reason=body.reason if body else None,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get(
    "/settings",
    response_model=list[PenaltySettingsOut],
    summary="Настройки пеней по СТ",
)
async def list_penalty_settings(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    repo=Depends(get_penalty_settings_repository),
    cooperative_id: UUID = Query(...),
) -> list[PenaltySettingsOut]:
    _financial_roles(current_user)
    cid = _coop(current_user, cooperative_id)
    rows = await repo.list_for_cooperative(cid)
    return [
        PenaltySettingsOut(
            id=r.id,
            cooperative_id=r.cooperative_id,
            contribution_type_id=r.contribution_type_id,
            is_enabled=r.is_enabled,
            daily_rate=r.daily_rate,
            grace_period_days=r.grace_period_days,
            effective_from=r.effective_from,
            effective_to=r.effective_to,
        )
        for r in rows
        if r.id is not None
    ]


@router.post(
    "/settings",
    response_model=PenaltySettingsOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создать настройки пеней",
)
async def create_penalty_settings(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    repo=Depends(get_penalty_settings_repository),
    cooperative_id: UUID = Query(...),
    body: PenaltySettingsCreate = ...,
) -> PenaltySettingsOut:
    _financial_roles(current_user)
    cid = _coop(current_user, cooperative_id)
    entity = PenaltySettings(
        id=uuid4(),
        cooperative_id=cid,
        contribution_type_id=body.contribution_type_id,
        is_enabled=body.is_enabled,
        daily_rate=body.daily_rate,
        grace_period_days=body.grace_period_days,
        effective_from=body.effective_from,
        effective_to=body.effective_to,
        created_at=datetime.now(UTC),
    )
    saved = await repo.add(entity)
    assert saved.id is not None
    return PenaltySettingsOut(
        id=saved.id,
        cooperative_id=saved.cooperative_id,
        contribution_type_id=saved.contribution_type_id,
        is_enabled=saved.is_enabled,
        daily_rate=saved.daily_rate,
        grace_period_days=saved.grace_period_days,
        effective_from=saved.effective_from,
        effective_to=saved.effective_to,
    )


@router.patch(
    "/settings/{settings_id}",
    response_model=PenaltySettingsOut,
    summary="Обновить настройки пеней",
)
async def update_penalty_settings(
    settings_id: UUID,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    repo=Depends(get_penalty_settings_repository),
    cooperative_id: UUID = Query(...),
    body: PenaltySettingsUpdate = ...,
) -> PenaltySettingsOut:
    _financial_roles(current_user)
    cid = _coop(current_user, cooperative_id)
    existing = await repo.get_by_id(settings_id, cid)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Настройки не найдены")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(existing, k, v)
    saved = await repo.update(existing)
    assert saved.id is not None
    return PenaltySettingsOut(
        id=saved.id,
        cooperative_id=saved.cooperative_id,
        contribution_type_id=saved.contribution_type_id,
        is_enabled=saved.is_enabled,
        daily_rate=saved.daily_rate,
        grace_period_days=saved.grace_period_days,
        effective_from=saved.effective_from,
        effective_to=saved.effective_to,
    )


@router.delete(
    "/settings/{settings_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить настройки пеней",
)
async def delete_penalty_settings(
    settings_id: UUID,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    repo=Depends(get_penalty_settings_repository),
    cooperative_id: UUID = Query(...),
) -> None:
    _financial_roles(current_user)
    cid = _coop(current_user, cooperative_id)
    await repo.delete(settings_id, cid)
