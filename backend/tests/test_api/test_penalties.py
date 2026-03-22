"""API пеней (фаза 5)."""

from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import create_access_token, get_password_hash
from app.modules.accruals.infrastructure.models import ContributionTypeModel as ContributionType
from app.modules.administration.infrastructure.models import AppUserModel as AppUser
from app.modules.cooperative_core.infrastructure.models import CooperativeModel as Cooperative


@pytest.fixture
async def admin_token(test_db) -> str:
    coop = Cooperative(name="СТ Пени")
    test_db.add(coop)
    await test_db.flush()
    admin = AppUser(
        username="pen_admin",
        email="pen@example.com",
        hashed_password=get_password_hash("x"),
        role="admin",
        is_active=True,
    )
    test_db.add(admin)
    await test_db.commit()
    return create_access_token(data={"sub": "pen_admin", "role": "admin"})


@pytest.mark.asyncio
async def test_penalties_calculate_empty(async_client: AsyncClient, admin_token: str, test_db) -> None:
    rdb = await test_db.execute(select(Cooperative).where(Cooperative.name == "СТ Пени"))
    coop = rdb.scalar_one()
    r = await async_client.get(
        "/api/penalties/calculate",
        params={"cooperative_id": str(coop.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_penalty_settings_crud(async_client: AsyncClient, admin_token: str, test_db) -> None:
    rdb = await test_db.execute(select(Cooperative).where(Cooperative.name == "СТ Пени"))
    coop = rdb.scalar_one()
    cid = str(coop.id)
    headers = {"Authorization": f"Bearer {admin_token}"}

    r = await async_client.post(
        "/api/penalties/settings",
        params={"cooperative_id": cid},
        json={
            "is_enabled": True,
            "daily_rate": "0.001",
            "grace_period_days": 5,
            "effective_from": "2026-01-01",
        },
        headers=headers,
    )
    assert r.status_code == 201
    sid = r.json()["id"]

    r2 = await async_client.get(
        "/api/penalties/settings",
        params={"cooperative_id": cid},
        headers=headers,
    )
    assert r2.status_code == 200
    assert len(r2.json()) == 1

    r3 = await async_client.patch(
        f"/api/penalties/settings/{sid}",
        params={"cooperative_id": cid},
        json={"grace_period_days": 7},
        headers=headers,
    )
    assert r3.status_code == 200
    assert r3.json()["grace_period_days"] == 7

    r4 = await async_client.delete(
        f"/api/penalties/settings/{sid}",
        params={"cooperative_id": cid},
        headers=headers,
    )
    assert r4.status_code == 204


@pytest.mark.asyncio
async def test_write_off_non_penalty_rejected(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
) -> None:
    coop = Cooperative(name="СТ2")
    test_db.add(coop)
    await test_db.flush()
    ct = ContributionType(name="Обычный", code="XMEM", description="")
    test_db.add(ct)
    await test_db.flush()
    from app.modules.accruals.infrastructure.models import AccrualModel as Accrual
    from app.modules.financial_core.infrastructure.models import FinancialSubjectModel as FS

    fs = FS(
        subject_type="LAND_PLOT",
        subject_id=coop.id,
        cooperative_id=coop.id,
        code="FS-PEN-TEST",
        status="active",
    )
    test_db.add(fs)
    await test_db.flush()
    acc = Accrual(
        financial_subject_id=fs.id,
        contribution_type_id=ct.id,
        amount=Decimal("10.00"),
        accrual_date=date(2026, 1, 1),
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        status="applied",
        operation_number="ACC-NON-PEN",
    )
    test_db.add(acc)
    await test_db.commit()

    r = await async_client.post(
        f"/api/penalties/{acc.id}/write-off",
        params={"cooperative_id": str(coop.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
        json={},
    )
    assert r.status_code == 400
