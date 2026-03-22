"""Интеграция фазы 5: начисление → DebtLine → платёж → расчёт/начисление пеней.

Покрывает сценарии из критерия приёмки phase-5-debt-penalties.md (полный цикл в API).
"""

from __future__ import annotations

import asyncio
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import create_access_token, get_password_hash
from app.modules.accruals.infrastructure.models import ContributionTypeModel as ContributionType
from app.modules.administration.infrastructure.models import AppUserModel as AppUser
from app.modules.cooperative_core.infrastructure.models import CooperativeModel as Cooperative
from app.modules.financial_core.infrastructure.models import DebtLineModel as DebtLine
from app.modules.financial_core.infrastructure.models import (
    FinancialSubjectModel as FinancialSubject,
)
from app.modules.land_management.infrastructure.models import LandPlotModel as LandPlot
from app.modules.land_management.infrastructure.models import OwnerModel as Owner
from app.modules.land_management.infrastructure.models import PlotOwnershipModel as PlotOwnership


async def _allow_event_handlers() -> None:
    """Обработчики событий ставятся в asyncio.create_task — дать циклу их отработать."""
    await asyncio.sleep(0.25)


async def _seed_coop_with_plot_and_types(test_db) -> dict[str, Any]:
    coop = Cooperative(name="СТ Фаза 5 интеграция", unp="333333333", address="Минск")
    test_db.add(coop)
    await test_db.flush()

    admin = AppUser(
        username="p5_int_admin",
        email="p5int@example.com",
        hashed_password=get_password_hash("x"),
        role="admin",
        is_active=True,
    )
    test_db.add(admin)
    await test_db.flush()

    plot = LandPlot(
        cooperative_id=coop.id,
        plot_number="P5-1",
        area_sqm=Decimal("600.00"),
        status="active",
    )
    test_db.add(plot)
    await test_db.flush()

    fs = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=plot.id,
        cooperative_id=coop.id,
        code="FS-P5-001",
        status="active",
    )
    test_db.add(fs)
    await test_db.flush()

    ct_member = ContributionType(
        name="Членский",
        code="MEMBER_P5_INT",
        description="",
        is_system=False,
    )
    ct_penalty = ContributionType(
        name="Пени",
        code="PENALTY",
        description="Системный",
        is_system=True,
    )
    test_db.add_all([ct_member, ct_penalty])
    await test_db.flush()

    owner = Owner(
        owner_type="physical",
        name="Должников Иван",
        tax_id="444444444B",
        contact_phone="+375000000001",
    )
    test_db.add(owner)
    await test_db.flush()

    ownership = PlotOwnership(
        land_plot_id=plot.id,
        owner_id=owner.id,
        is_primary=True,
        share_numerator=1,
        share_denominator=1,
        valid_from=date(2024, 1, 1),
    )
    test_db.add(ownership)
    await test_db.commit()

    return {
        "coop_id": coop.id,
        "fs_id": fs.id,
        "ct_member_id": ct_member.id,
        "ct_penalty_id": ct_penalty.id,
        "owner_id": owner.id,
        "admin_token": create_access_token(data={"sub": "p5_int_admin", "role": "admin"}),
    }


@pytest.fixture
async def phase5_world(test_db) -> dict[str, Any]:
    return await _seed_coop_with_plot_and_types(test_db)


@pytest.mark.asyncio
async def test_phase5_full_cycle_accrual_debt_partial_payment_penalty(
    async_client: AsyncClient,
    phase5_world: dict[str, Any],
    test_db,
) -> None:
    """Начисление с due_date → DebtLine → частичный платёж → база пени от остатка."""
    cid = str(phase5_world["coop_id"])
    fs_id = phase5_world["fs_id"]
    ct_id = str(phase5_world["ct_member_id"])
    owner_id = str(phase5_world["owner_id"])
    headers = {"Authorization": f"Bearer {phase5_world['admin_token']}"}

    due = date(2024, 6, 1)
    r_acc = await async_client.post(
        f"/api/accruals/?cooperative_id={cid}",
        json={
            "financial_subject_id": str(fs_id),
            "contribution_type_id": ct_id,
            "amount": "200.00",
            "accrual_date": "2024-05-15",
            "period_start": "2024-05-01",
            "period_end": "2024-05-31",
            "due_date": due.isoformat(),
        },
        headers=headers,
    )
    assert r_acc.status_code == 201, r_acc.text
    accrual_id = r_acc.json()["id"]

    r_apply = await async_client.post(
        f"/api/accruals/{accrual_id}/apply?cooperative_id={cid}",
        headers=headers,
    )
    assert r_apply.status_code == 200, r_apply.text

    await _allow_event_handlers()

    dl_row = await test_db.execute(select(DebtLine).where(DebtLine.accrual_id == UUID(accrual_id)))
    dl = dl_row.scalar_one_or_none()
    assert dl is not None
    assert dl.status == "active"
    assert dl.paid_amount == Decimal("0")
    assert dl.original_amount == Decimal("200.00")

    await async_client.post(
        "/api/penalties/settings",
        params={"cooperative_id": cid},
        json={
            "is_enabled": True,
            "daily_rate": "0.01",
            "grace_period_days": 0,
            "effective_from": "2024-01-01",
        },
        headers=headers,
    )

    as_of = date(2024, 6, 10)
    r_calc1 = await async_client.get(
        "/api/penalties/calculate",
        params={"cooperative_id": cid, "as_of_date": as_of.isoformat()},
        headers=headers,
    )
    assert r_calc1.status_code == 200
    rows1 = r_calc1.json()
    assert len(rows1) == 1
    p1 = Decimal(rows1[0]["penalty_amount"])
    assert p1 > 0

    r_pay = await async_client.post(
        f"/api/payments/?cooperative_id={cid}",
        json={
            "financial_subject_id": str(fs_id),
            "payer_owner_id": owner_id,
            "amount": "50.00",
            "payment_date": "2024-06-05",
            "document_number": "P5-PARTIAL",
        },
        headers=headers,
    )
    assert r_pay.status_code == 201, r_pay.text

    await _allow_event_handlers()

    test_db.expire_all()
    dl_row2 = await test_db.execute(select(DebtLine).where(DebtLine.accrual_id == UUID(accrual_id)))
    dl2 = dl_row2.scalar_one()
    assert dl2.paid_amount == Decimal("50.00")
    assert dl2.status == "active"

    r_calc2 = await async_client.get(
        "/api/penalties/calculate",
        params={"cooperative_id": cid, "as_of_date": as_of.isoformat()},
        headers=headers,
    )
    assert r_calc2.status_code == 200
    rows2 = r_calc2.json()
    assert len(rows2) == 1
    p2 = Decimal(rows2[0]["penalty_amount"])
    assert p2 < p1
    assert rows2[0]["outstanding"] == "150.00"


@pytest.mark.asyncio
async def test_phase5_accrue_penalties_idempotent(
    async_client: AsyncClient,
    phase5_world: dict[str, Any],
    test_db,
) -> None:
    """AccruePenalties создаёт начисления PENALTY; повтор без дублей."""
    cid = str(phase5_world["coop_id"])
    fs_id = phase5_world["fs_id"]
    ct_id = str(phase5_world["ct_member_id"])
    pen_ct = str(phase5_world["ct_penalty_id"])
    headers = {"Authorization": f"Bearer {phase5_world['admin_token']}"}

    r_acc = await async_client.post(
        f"/api/accruals/?cooperative_id={cid}",
        json={
            "financial_subject_id": str(fs_id),
            "contribution_type_id": ct_id,
            "amount": "100.00",
            "accrual_date": "2024-03-01",
            "period_start": "2024-03-01",
            "period_end": "2024-03-31",
            "due_date": "2024-03-10",
        },
        headers=headers,
    )
    aid = r_acc.json()["id"]
    await async_client.post(
        f"/api/accruals/{aid}/apply?cooperative_id={cid}",
        headers=headers,
    )

    await async_client.post(
        "/api/penalties/settings",
        params={"cooperative_id": cid},
        json={
            "is_enabled": True,
            "daily_rate": "0.02",
            "grace_period_days": 0,
            "effective_from": "2024-01-01",
        },
        headers=headers,
    )

    as_of = "2024-03-20"
    r1 = await async_client.post(
        "/api/penalties/accrue",
        params={"cooperative_id": cid, "as_of_date": as_of},
        headers=headers,
    )
    assert r1.status_code == 200, r1.text
    ids1 = r1.json()
    assert len(ids1) >= 1

    r2 = await async_client.post(
        "/api/penalties/accrue",
        params={"cooperative_id": cid, "as_of_date": as_of},
        headers=headers,
    )
    assert r2.status_code == 200
    assert r2.json() == []

    r_list = await async_client.get(
        "/api/accruals/",
        params={"cooperative_id": cid, "financial_subject_id": str(fs_id)},
        headers=headers,
    )
    assert r_list.status_code == 200
    penalty_accruals = [a for a in r_list.json() if a["contribution_type_id"] == pen_ct]
    assert len(penalty_accruals) == 1
    assert penalty_accruals[0]["status"] == "applied"


@pytest.mark.asyncio
async def test_phase5_full_payment_principal_penalty_calculation_zero(
    async_client: AsyncClient,
    phase5_world: dict[str, Any],
    test_db,
) -> None:
    """После полного погашения строки долга расчёт пеней по ней пустой (остаток 0)."""
    cid = str(phase5_world["coop_id"])
    fs_id = phase5_world["fs_id"]
    ct_id = str(phase5_world["ct_member_id"])
    owner_id = str(phase5_world["owner_id"])
    headers = {"Authorization": f"Bearer {phase5_world['admin_token']}"}

    r_acc = await async_client.post(
        f"/api/accruals/?cooperative_id={cid}",
        json={
            "financial_subject_id": str(fs_id),
            "contribution_type_id": ct_id,
            "amount": "80.00",
            "accrual_date": "2024-07-01",
            "period_start": "2024-07-01",
            "period_end": "2024-07-31",
            "due_date": "2024-07-05",
        },
        headers=headers,
    )
    aid = r_acc.json()["id"]
    await async_client.post(f"/api/accruals/{aid}/apply?cooperative_id={cid}", headers=headers)

    await async_client.post(
        "/api/penalties/settings",
        params={"cooperative_id": cid},
        json={
            "is_enabled": True,
            "daily_rate": "0.05",
            "grace_period_days": 0,
            "effective_from": "2024-01-01",
        },
        headers=headers,
    )

    r_before = await async_client.get(
        "/api/penalties/calculate",
        params={"cooperative_id": cid, "as_of_date": "2024-07-20"},
        headers=headers,
    )
    assert len(r_before.json()) == 1

    r_pay = await async_client.post(
        f"/api/payments/?cooperative_id={cid}",
        json={
            "financial_subject_id": str(fs_id),
            "payer_owner_id": owner_id,
            "amount": "80.00",
            "payment_date": "2024-07-10",
            "document_number": "P5-FULL",
        },
        headers=headers,
    )
    assert r_pay.status_code == 201, r_pay.text

    await _allow_event_handlers()

    dl_row = await test_db.execute(select(DebtLine).where(DebtLine.accrual_id == UUID(aid)))
    assert dl_row.scalar_one().status == "paid"

    r_after = await async_client.get(
        "/api/penalties/calculate",
        params={"cooperative_id": cid, "as_of_date": "2024-07-20"},
        headers=headers,
    )
    assert r_after.json() == []


@pytest.mark.asyncio
async def test_phase5_grace_period_api_no_penalty(
    async_client: AsyncClient,
    phase5_world: dict[str, Any],
) -> None:
    """До окончания льготного периода предрасчёт пеней пустой."""
    cid = str(phase5_world["coop_id"])
    fs_id = phase5_world["fs_id"]
    ct_id = str(phase5_world["ct_member_id"])
    headers = {"Authorization": f"Bearer {phase5_world['admin_token']}"}

    r_acc = await async_client.post(
        f"/api/accruals/?cooperative_id={cid}",
        json={
            "financial_subject_id": str(fs_id),
            "contribution_type_id": ct_id,
            "amount": "40.00",
            "accrual_date": "2024-08-01",
            "period_start": "2024-08-01",
            "period_end": "2024-08-31",
            "due_date": "2024-08-10",
        },
        headers=headers,
    )
    aid = r_acc.json()["id"]
    await async_client.post(f"/api/accruals/{aid}/apply?cooperative_id={cid}", headers=headers)

    await async_client.post(
        "/api/penalties/settings",
        params={"cooperative_id": cid},
        json={
            "is_enabled": True,
            "daily_rate": "1",
            "grace_period_days": 10,
            "effective_from": "2024-01-01",
        },
        headers=headers,
    )

    r_calc = await async_client.get(
        "/api/penalties/calculate",
        params={"cooperative_id": cid, "as_of_date": "2024-08-20"},
        headers=headers,
    )
    assert r_calc.status_code == 200
    assert r_calc.json() == []


@pytest.mark.asyncio
async def test_phase5_write_off_penalty_after_accrue(
    async_client: AsyncClient,
    phase5_world: dict[str, Any],
) -> None:
    """Начислили пени через accrue → write-off снимает начисление PENALTY."""
    cid = str(phase5_world["coop_id"])
    fs_id = phase5_world["fs_id"]
    ct_id = str(phase5_world["ct_member_id"])
    headers = {"Authorization": f"Bearer {phase5_world['admin_token']}"}

    r_acc = await async_client.post(
        f"/api/accruals/?cooperative_id={cid}",
        json={
            "financial_subject_id": str(fs_id),
            "contribution_type_id": ct_id,
            "amount": "100.00",
            "accrual_date": "2024-09-01",
            "period_start": "2024-09-01",
            "period_end": "2024-09-30",
            "due_date": "2024-09-05",
        },
        headers=headers,
    )
    aid = r_acc.json()["id"]
    await async_client.post(f"/api/accruals/{aid}/apply?cooperative_id={cid}", headers=headers)

    await async_client.post(
        "/api/penalties/settings",
        params={"cooperative_id": cid},
        json={
            "is_enabled": True,
            "daily_rate": "0.01",
            "grace_period_days": 0,
            "effective_from": "2024-01-01",
        },
        headers=headers,
    )

    r_accrue = await async_client.post(
        "/api/penalties/accrue",
        params={"cooperative_id": cid, "as_of_date": "2024-09-15"},
        headers=headers,
    )
    assert r_accrue.status_code == 200
    pen_ids = r_accrue.json()
    assert len(pen_ids) == 1
    pen_aid = str(pen_ids[0])

    r_wo = await async_client.post(
        f"/api/penalties/{pen_aid}/write-off",
        params={"cooperative_id": cid},
        headers=headers,
        json={"reason": "Тест списания"},
    )
    assert r_wo.status_code == 204

    r_get = await async_client.get(
        "/api/accruals/",
        params={"cooperative_id": cid, "financial_subject_id": str(fs_id)},
        headers=headers,
    )
    pen_row = next(a for a in r_get.json() if a["id"] == pen_aid)
    assert pen_row["status"] == "cancelled"


@pytest.mark.asyncio
async def test_phase5_penalties_disabled_settings_empty_calculate(
    async_client: AsyncClient,
    phase5_world: dict[str, Any],
) -> None:
    """Отключённые настройки (is_enabled=false) — расчёт не возвращает строк."""
    cid = str(phase5_world["coop_id"])
    fs_id = phase5_world["fs_id"]
    ct_id = str(phase5_world["ct_member_id"])
    headers = {"Authorization": f"Bearer {phase5_world['admin_token']}"}

    r_acc = await async_client.post(
        f"/api/accruals/?cooperative_id={cid}",
        json={
            "financial_subject_id": str(fs_id),
            "contribution_type_id": ct_id,
            "amount": "30.00",
            "accrual_date": "2024-10-01",
            "period_start": "2024-10-01",
            "period_end": "2024-10-31",
            "due_date": "2024-10-02",
        },
        headers=headers,
    )
    aid = r_acc.json()["id"]
    await async_client.post(f"/api/accruals/{aid}/apply?cooperative_id={cid}", headers=headers)

    await async_client.post(
        "/api/penalties/settings",
        params={"cooperative_id": cid},
        json={
            "is_enabled": False,
            "daily_rate": "0.5",
            "grace_period_days": 0,
            "effective_from": "2024-01-01",
        },
        headers=headers,
    )

    r_calc = await async_client.get(
        "/api/penalties/calculate",
        params={"cooperative_id": cid, "as_of_date": "2024-10-20"},
        headers=headers,
    )
    assert r_calc.json() == []
