"""Интеграционные тесты фазы 4: финансовые периоды, снимки баланса, оборотная ведомость."""

from __future__ import annotations

from calendar import monthrange
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select, update

from app.core.security import create_access_token, get_password_hash
from app.modules.accruals.infrastructure.models import ContributionTypeModel as ContributionType
from app.modules.administration.infrastructure.models import AppUserModel as AppUser
from app.modules.cooperative_core.infrastructure.models import CooperativeModel as Cooperative
from app.modules.financial_core.infrastructure.models import (
    BalanceSnapshotModel,
    FinancialPeriodModel,
)
from app.modules.financial_core.infrastructure.models import (
    FinancialSubjectModel as FinancialSubject,
)
from app.modules.land_management.infrastructure.models import LandPlotModel as LandPlot
from app.modules.land_management.infrastructure.models import OwnerModel as Owner


async def _seed_phase4_world(test_db) -> dict[str, Any]:
    """СТ, пользователи, участок, фин. субъект, вид взноса, владелец."""
    coop = Cooperative(name="СТ Фаза 4", unp="111111111", address="Минск")
    test_db.add(coop)
    await test_db.flush()

    admin = AppUser(
        username="p4_admin",
        email="p4_admin@example.com",
        hashed_password=get_password_hash("x"),
        role="admin",
        is_active=True,
    )
    chairman = AppUser(
        username="p4_chair",
        email="p4_chair@example.com",
        hashed_password=get_password_hash("x"),
        role="chairman",
        cooperative_id=coop.id,
        is_active=True,
    )
    treasurer = AppUser(
        username="p4_treas",
        email="p4_treas@example.com",
        hashed_password=get_password_hash("x"),
        role="treasurer",
        cooperative_id=coop.id,
        is_active=True,
    )
    test_db.add_all([admin, chairman, treasurer])
    await test_db.flush()

    plot = LandPlot(
        cooperative_id=coop.id,
        plot_number="P4-1",
        area_sqm=Decimal("600.00"),
        status="active",
    )
    test_db.add(plot)
    await test_db.flush()

    fs = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=plot.id,
        cooperative_id=coop.id,
        code="FS-P4-001",
        status="active",
    )
    test_db.add(fs)
    await test_db.flush()

    ct = ContributionType(name="Членский", code="MEMBER_P4", description="")
    test_db.add(ct)
    await test_db.flush()

    owner = Owner(
        owner_type="physical",
        name="Тестов Владелец",
        tax_id="222222222B",
        contact_phone="+375000000000",
    )
    test_db.add(owner)
    await test_db.commit()

    return {
        "coop_id": coop.id,
        "fs_id": fs.id,
        "ct_id": ct.id,
        "owner_id": owner.id,
        "admin_token": create_access_token(data={"sub": "p4_admin", "role": "admin"}),
        "chairman_token": create_access_token(data={"sub": "p4_chair", "role": "chairman"}),
        "treasurer_token": create_access_token(data={"sub": "p4_treas", "role": "treasurer"}),
    }


@pytest.fixture
async def phase4(test_db) -> dict[str, Any]:
    return await _seed_phase4_world(test_db)


@pytest.mark.asyncio
async def test_create_list_financial_period(
    async_client: AsyncClient,
    phase4: dict[str, Any],
) -> None:
    cid = phase4["coop_id"]
    r = await async_client.post(
        f"/api/financial-subjects/periods?cooperative_id={cid}",
        json={"period_type": "monthly", "year": 2025, "month": 4},
        headers={"Authorization": f"Bearer {phase4['chairman_token']}"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "open"
    assert body["year"] == 2025
    assert body["month"] == 4

    r2 = await async_client.get(
        f"/api/financial-subjects/periods?cooperative_id={cid}&year=2025",
        headers={"Authorization": f"Bearer {phase4['admin_token']}"},
    )
    assert r2.status_code == 200
    months = {p["month"] for p in r2.json()}
    assert 4 in months


@pytest.mark.asyncio
async def test_cannot_close_period_while_previous_month_open(
    async_client: AsyncClient,
    phase4: dict[str, Any],
) -> None:
    cid = phase4["coop_id"]
    headers_a = {"Authorization": f"Bearer {phase4['admin_token']}"}
    headers_t = {"Authorization": f"Bearer {phase4['treasurer_token']}"}

    for month in (3, 4):
        r = await async_client.post(
            f"/api/financial-subjects/periods?cooperative_id={cid}",
            json={"period_type": "monthly", "year": 2025, "month": month},
            headers=headers_a,
        )
        assert r.status_code == 201, r.text

    r_list = await async_client.get(
        f"/api/financial-subjects/periods?cooperative_id={cid}&year=2025",
        headers=headers_a,
    )
    periods = {p["month"]: p for p in r_list.json()}
    april_id = periods[4]["id"]

    r_close = await async_client.post(
        f"/api/financial-subjects/periods/{april_id}/close?cooperative_id={cid}",
        json={},
        headers=headers_t,
    )
    assert r_close.status_code == 400
    assert "предыдущий" in r_close.json()["detail"].lower() or "закрыт" in r_close.json()[
        "detail"
    ].lower()

    march_id = periods[3]["id"]
    r_ok = await async_client.post(
        f"/api/financial-subjects/periods/{march_id}/close?cooperative_id={cid}",
        json={},
        headers=headers_t,
    )
    assert r_ok.status_code == 200, r_ok.text

    r_close2 = await async_client.post(
        f"/api/financial-subjects/periods/{april_id}/close?cooperative_id={cid}",
        json={},
        headers=headers_t,
    )
    assert r_close2.status_code == 200


@pytest.mark.asyncio
async def test_close_creates_snapshots_balance_and_turnover(
    async_client: AsyncClient,
    phase4: dict[str, Any],
    test_db,
) -> None:
    # ADR 0002: date(created_at) <= as_of_date — даты операций в текущем месяце,
    # снимок на последний день месяца (день создания записей <= as_of_date).
    today = date.today()
    year, month = today.year, today.month
    _, last_day = monthrange(year, month)
    accrual_day = min(max(today.day, 5), last_day)
    payment_day = min(accrual_day + 3, last_day)
    accrual_date_str = date(year, month, accrual_day).isoformat()
    payment_date_str = date(year, month, payment_day).isoformat()
    period_end_str = date(year, month, last_day).isoformat()

    cid = str(phase4["coop_id"])
    fs_id = phase4["fs_id"]
    ct_id = phase4["ct_id"]
    owner_id = phase4["owner_id"]
    headers_a = {"Authorization": f"Bearer {phase4['admin_token']}"}
    headers_t = {"Authorization": f"Bearer {phase4['treasurer_token']}"}

    r_p = await async_client.post(
        f"/api/financial-subjects/periods?cooperative_id={cid}",
        json={"period_type": "monthly", "year": year, "month": month},
        headers=headers_a,
    )
    assert r_p.status_code == 201
    period_id = UUID(r_p.json()["id"])

    r_acc = await async_client.post(
        f"/api/accruals/?cooperative_id={cid}",
        json={
            "financial_subject_id": str(fs_id),
            "contribution_type_id": str(ct_id),
            "amount": "1000.00",
            "accrual_date": accrual_date_str,
            "period_start": date(year, 1, 1).isoformat(),
            "period_end": period_end_str,
        },
        headers=headers_a,
    )
    assert r_acc.status_code == 201, r_acc.text
    accrual_uuid = r_acc.json()["id"]

    r_apply = await async_client.post(
        f"/api/accruals/{accrual_uuid}/apply?cooperative_id={cid}",
        headers=headers_a,
    )
    assert r_apply.status_code == 200

    r_pay = await async_client.post(
        f"/api/payments/?cooperative_id={cid}",
        json={
            "financial_subject_id": str(fs_id),
            "payer_owner_id": str(owner_id),
            "amount": "300.00",
            "payment_date": payment_date_str,
            "document_number": "P4-1",
        },
        headers=headers_a,
    )
    assert r_pay.status_code == 201, r_pay.text

    r_close = await async_client.post(
        f"/api/financial-subjects/periods/{period_id}/close?cooperative_id={cid}",
        json={},
        headers=headers_t,
    )
    assert r_close.status_code == 200

    q = await test_db.execute(
        select(func.count()).select_from(BalanceSnapshotModel).where(
            BalanceSnapshotModel.period_id == period_id,
            BalanceSnapshotModel.financial_subject_id == fs_id,
        )
    )
    assert q.scalar_one() == 1

    r_bal = await async_client.get(
        f"/api/financial-subjects/{fs_id}/balance?cooperative_id={cid}&as_of_date={period_end_str}",
        headers=headers_a,
    )
    assert r_bal.status_code == 200
    bal = r_bal.json()
    assert Decimal(bal["total_accruals"]) == Decimal("1000.00")
    assert Decimal(bal["total_payments"]) == Decimal("300.00")
    assert Decimal(bal["balance"]) == Decimal("700.00")

    r_to = await async_client.get(
        f"/api/reports/turnover?cooperative_id={cid}&year={year}&month={month}",
        headers=headers_a,
    )
    assert r_to.status_code == 200
    rows = r_to.json()
    row = next(r for r in rows if r["financial_subject_id"] == str(fs_id))
    assert Decimal(row["accrued_in_period"]) == Decimal("1000.00")
    assert Decimal(row["paid_in_period"]) == Decimal("300.00")
    assert Decimal(row["closing_balance"]) == Decimal("700.00")


@pytest.mark.asyncio
async def test_accrual_create_blocked_in_closed_period(
    async_client: AsyncClient,
    phase4: dict[str, Any],
) -> None:
    cid = str(phase4["coop_id"])
    fs_id = phase4["fs_id"]
    ct_id = phase4["ct_id"]
    headers_a = {"Authorization": f"Bearer {phase4['admin_token']}"}
    headers_t = {"Authorization": f"Bearer {phase4['treasurer_token']}"}

    r_p = await async_client.post(
        f"/api/financial-subjects/periods?cooperative_id={cid}",
        json={"period_type": "monthly", "year": 2025, "month": 7},
        headers=headers_a,
    )
    assert r_p.status_code == 201
    pid = r_p.json()["id"]

    r_close = await async_client.post(
        f"/api/financial-subjects/periods/{pid}/close?cooperative_id={cid}",
        json={},
        headers=headers_t,
    )
    assert r_close.status_code == 200

    r_acc = await async_client.post(
        f"/api/accruals/?cooperative_id={cid}",
        json={
            "financial_subject_id": str(fs_id),
            "contribution_type_id": str(ct_id),
            "amount": "100.00",
            "accrual_date": "2025-07-20",
            "period_start": "2025-07-01",
            "period_end": "2025-07-31",
        },
        headers=headers_a,
    )
    assert r_acc.status_code == 403
    assert "период" in r_acc.json()["detail"].lower()


@pytest.mark.asyncio
async def test_treasurer_reopen_within_window_admin_reopen_locked(
    async_client: AsyncClient,
    phase4: dict[str, Any],
    test_db,
) -> None:
    cid = str(phase4["coop_id"])
    headers_a = {"Authorization": f"Bearer {phase4['admin_token']}"}
    headers_t = {"Authorization": f"Bearer {phase4['treasurer_token']}"}

    r_p = await async_client.post(
        f"/api/financial-subjects/periods?cooperative_id={cid}",
        json={"period_type": "monthly", "year": 2025, "month": 8},
        headers=headers_a,
    )
    pid = r_p.json()["id"]

    await async_client.post(
        f"/api/financial-subjects/periods/{pid}/close?cooperative_id={cid}",
        json={},
        headers=headers_t,
    )

    r_ro = await async_client.post(
        f"/api/financial-subjects/periods/{pid}/reopen?cooperative_id={cid}",
        json={},
        headers=headers_t,
    )
    assert r_ro.status_code == 200
    assert r_ro.json()["status"] == "open"

    await async_client.post(
        f"/api/financial-subjects/periods/{pid}/close?cooperative_id={cid}",
        json={},
        headers=headers_t,
    )

    old_closed = datetime.now(UTC) - timedelta(days=40)
    await test_db.execute(
        update(FinancialPeriodModel)
        .where(FinancialPeriodModel.id == UUID(pid))
        .values(closed_at=old_closed)
    )
    await test_db.commit()

    await async_client.get(
        f"/api/financial-subjects/periods?cooperative_id={cid}&year=2025",
        headers=headers_a,
    )

    r_fail = await async_client.post(
        f"/api/financial-subjects/periods/{pid}/reopen?cooperative_id={cid}",
        json={},
        headers=headers_t,
    )
    assert r_fail.status_code == 400

    r_admin = await async_client.post(
        f"/api/financial-subjects/periods/{pid}/reopen?cooperative_id={cid}",
        json={},
        headers=headers_a,
    )
    assert r_admin.status_code == 200
    assert r_admin.json()["status"] == "open"


@pytest.mark.asyncio
async def test_reopen_deletes_snapshots(
    async_client: AsyncClient,
    phase4: dict[str, Any],
    test_db,
) -> None:
    cid = str(phase4["coop_id"])
    fs_id = phase4["fs_id"]
    ct_id = phase4["ct_id"]
    headers_a = {"Authorization": f"Bearer {phase4['admin_token']}"}
    headers_t = {"Authorization": f"Bearer {phase4['treasurer_token']}"}

    r_p = await async_client.post(
        f"/api/financial-subjects/periods?cooperative_id={cid}",
        json={"period_type": "monthly", "year": 2025, "month": 9},
        headers=headers_a,
    )
    period_id = UUID(r_p.json()["id"])

    r_acc = await async_client.post(
        f"/api/accruals/?cooperative_id={cid}",
        json={
            "financial_subject_id": str(fs_id),
            "contribution_type_id": str(ct_id),
            "amount": "50.00",
            "accrual_date": "2025-09-05",
            "period_start": "2025-09-01",
            "period_end": "2025-09-30",
        },
        headers=headers_a,
    )
    aid = r_acc.json()["id"]
    await async_client.post(
        f"/api/accruals/{aid}/apply?cooperative_id={cid}",
        headers=headers_a,
    )

    await async_client.post(
        f"/api/financial-subjects/periods/{period_id}/close?cooperative_id={cid}",
        json={},
        headers=headers_t,
    )

    q1 = await test_db.execute(
        select(func.count()).select_from(BalanceSnapshotModel).where(
            BalanceSnapshotModel.period_id == period_id
        )
    )
    assert q1.scalar_one() >= 1

    await async_client.post(
        f"/api/financial-subjects/periods/{period_id}/reopen?cooperative_id={cid}",
        json={},
        headers=headers_t,
    )

    q2 = await test_db.execute(
        select(func.count()).select_from(BalanceSnapshotModel).where(
            BalanceSnapshotModel.period_id == period_id
        )
    )
    assert q2.scalar_one() == 0


@pytest.mark.asyncio
async def test_only_admin_can_lock_period(
    async_client: AsyncClient,
    phase4: dict[str, Any],
) -> None:
    cid = str(phase4["coop_id"])
    headers_a = {"Authorization": f"Bearer {phase4['admin_token']}"}
    headers_t = {"Authorization": f"Bearer {phase4['treasurer_token']}"}

    r_p = await async_client.post(
        f"/api/financial-subjects/periods?cooperative_id={cid}",
        json={"period_type": "monthly", "year": 2025, "month": 10},
        headers=headers_a,
    )
    pid = r_p.json()["id"]
    await async_client.post(
        f"/api/financial-subjects/periods/{pid}/close?cooperative_id={cid}",
        json={},
        headers=headers_t,
    )

    r_denied = await async_client.post(
        f"/api/financial-subjects/periods/{pid}/lock?cooperative_id={cid}",
        headers=headers_t,
    )
    assert r_denied.status_code == 403

    r_ok = await async_client.post(
        f"/api/financial-subjects/periods/{pid}/lock?cooperative_id={cid}",
        headers=headers_a,
    )
    assert r_ok.status_code == 200
    assert r_ok.json()["status"] == "locked"


@pytest.mark.asyncio
async def test_cooperative_period_reopen_days_used_on_reopen(
    async_client: AsyncClient,
    test_db,
) -> None:
    """PATCH СТ задаёт окно; казначей не переоткрывает после истечения."""
    coop = Cooperative(name="СТ Окно переоткрытия", unp="333333333", address="")
    test_db.add(coop)
    await test_db.flush()

    treasurer = AppUser(
        username="p4_treas2",
        email="p4_t2@example.com",
        hashed_password=get_password_hash("x"),
        role="treasurer",
        cooperative_id=coop.id,
        is_active=True,
    )
    admin = AppUser(
        username="p4_admin2",
        email="p4_a2@example.com",
        hashed_password=get_password_hash("x"),
        role="admin",
        is_active=True,
    )
    test_db.add_all([treasurer, admin])
    await test_db.commit()

    admin_tok = create_access_token(data={"sub": "p4_admin2", "role": "admin"})
    treas_tok = create_access_token(data={"sub": "p4_treas2", "role": "treasurer"})
    cid = str(coop.id)
    headers_a = {"Authorization": f"Bearer {admin_tok}"}
    headers_t = {"Authorization": f"Bearer {treas_tok}"}

    await async_client.patch(
        f"/api/cooperatives/{cid}",
        json={"period_reopen_allowed_days": 5},
        headers=headers_a,
    )

    r_p = await async_client.post(
        f"/api/financial-subjects/periods?cooperative_id={cid}",
        json={"period_type": "monthly", "year": 2025, "month": 11},
        headers=headers_a,
    )
    assert r_p.status_code == 201
    pid = r_p.json()["id"]

    await async_client.post(
        f"/api/financial-subjects/periods/{pid}/close?cooperative_id={cid}",
        json={},
        headers=headers_t,
    )

    await test_db.execute(
        update(FinancialPeriodModel)
        .where(FinancialPeriodModel.id == UUID(pid))
        .values(closed_at=datetime.now(UTC) - timedelta(days=10))
    )
    await test_db.commit()

    r_fail = await async_client.post(
        f"/api/financial-subjects/periods/{pid}/reopen?cooperative_id={cid}",
        json={},
        headers=headers_t,
    )
    assert r_fail.status_code == 400
    detail = r_fail.json()["detail"]
    # Окно истекло → auto-lock, затем казначею запрещено (или явное «больше N дней»)
    assert "администратор" in detail.lower() or "5" in detail or "days" in detail.lower()
