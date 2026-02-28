from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, get_password_hash

# Import models from Clean Architecture modules
from app.modules.administration.infrastructure.models import AppUserModel as AppUser
from app.modules.cooperative_core.infrastructure.models import CooperativeModel as Cooperative
from app.modules.land_management.infrastructure.models import LandPlotModel as LandPlot
from app.modules.financial_core.infrastructure.models import FinancialSubjectModel as FinancialSubject
from app.modules.accruals.infrastructure.models import (
    AccrualModel as Accrual,
    ContributionTypeModel as ContributionType,
)


@pytest.fixture
async def admin_token(test_db) -> str:
    """Создаёт admin пользователя и возвращает токен."""
    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    admin = AppUser(
        username="admin_user",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass"),
        role="admin",
        is_active=True,
    )
    test_db.add(admin)
    await test_db.commit()

    return create_access_token(data={"sub": "admin_user", "role": "admin"})


@pytest.fixture
async def treasurer_token(test_db) -> str:
    """Создаёт treasurer пользователя с СТ и возвращает токен."""
    coop = Cooperative(name="СТ Казначея")
    test_db.add(coop)
    await test_db.flush()

    treasurer = AppUser(
        username="treasurer_user",
        email="treasurer@example.com",
        hashed_password=get_password_hash("treasurerpass"),
        role="treasurer",
        cooperative_id=coop.id,
        is_active=True,
    )
    test_db.add(treasurer)
    await test_db.commit()

    return create_access_token(data={"sub": "treasurer_user", "role": "treasurer"})


@pytest.fixture
async def contribution_type_fixture(test_db) -> ContributionType:
    """Создаёт вид взноса."""
    ct = ContributionType(
        name="Членский взнос", code="MEMBER", description="Ежегодный членский взнос"
    )
    test_db.add(ct)
    await test_db.commit()
    return ct


@pytest.fixture
async def financial_subject_fixture(test_db) -> FinancialSubject:
    """Создаёт финансовый субъект (участок)."""
    coop = Cooperative(name="СТ Для начислений")
    test_db.add(coop)
    await test_db.flush()

    plot = LandPlot(
        cooperative_id=coop.id, plot_number="Начисления Тест", area_sqm=Decimal("600.00")
    )
    test_db.add(plot)
    await test_db.flush()

    subject = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=plot.id,
        cooperative_id=coop.id,
    )
    test_db.add(subject)
    await test_db.commit()
    return subject


@pytest.mark.asyncio
async def test_create_accrual(
    async_client: AsyncClient,
    admin_token: str,
    financial_subject_fixture: FinancialSubject,
    contribution_type_fixture: ContributionType,
) -> None:
    """Тест создания начисления."""
    subject = financial_subject_fixture
    ct = contribution_type_fixture

    response = await async_client.post(
        "/api/v1/accruals/",
        json={
            "financial_subject_id": str(subject.id),
            "contribution_type_id": str(ct.id),
            "amount": "1500.00",
            "accrual_date": str(date.today()),
            "period_start": str(date.today().replace(month=1, day=1)),
            "period_end": str(date.today().replace(month=12, day=31)),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == "1500.00"
    assert data["status"] == "created"


@pytest.mark.asyncio
async def test_apply_accrual(
    async_client: AsyncClient,
    admin_token: str,
    financial_subject_fixture: FinancialSubject,
    contribution_type_fixture: ContributionType,
    test_db,
) -> None:
    """Тест применения начисления (created → applied)."""
    subject = financial_subject_fixture
    ct = contribution_type_fixture

    # Создаём начисление
    accrual = Accrual(
        financial_subject_id=subject.id,
        contribution_type_id=ct.id,
        amount=Decimal("1000.00"),
        accrual_date=date.today(),
        period_start=date.today().replace(month=1, day=1),
        status="created",
    )
    test_db.add(accrual)
    await test_db.commit()

    # Применяем
    response = await async_client.post(
        f"/api/v1/accruals/{accrual.id}/apply",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "applied"


@pytest.mark.asyncio
async def test_cancel_accrual(
    async_client: AsyncClient,
    admin_token: str,
    financial_subject_fixture: FinancialSubject,
    contribution_type_fixture: ContributionType,
    test_db,
) -> None:
    """Тест отмены начисления (applied → cancelled)."""
    subject = financial_subject_fixture
    ct = contribution_type_fixture

    # Создаём начисление со статусом applied
    accrual = Accrual(
        financial_subject_id=subject.id,
        contribution_type_id=ct.id,
        amount=Decimal("1000.00"),
        accrual_date=date.today(),
        period_start=date.today().replace(month=1, day=1),
        status="applied",
    )
    test_db.add(accrual)
    await test_db.commit()

    # Отменяем
    response = await async_client.post(
        f"/api/v1/accruals/{accrual.id}/cancel",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_already_cancelled_accrual(
    async_client: AsyncClient,
    admin_token: str,
    financial_subject_fixture: FinancialSubject,
    contribution_type_fixture: ContributionType,
    test_db,
) -> None:
    """Тест 400 при попытке отменить уже отменённое начисление."""
    subject = financial_subject_fixture
    ct = contribution_type_fixture

    # Создаём отменённое начисление
    accrual = Accrual(
        financial_subject_id=subject.id,
        contribution_type_id=ct.id,
        amount=Decimal("1000.00"),
        accrual_date=date.today(),
        period_start=date.today().replace(month=1, day=1),
        status="cancelled",
    )
    test_db.add(accrual)
    await test_db.commit()

    # Пытаемся отменить
    response = await async_client.post(
        f"/api/v1/accruals/{accrual.id}/cancel",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_apply_non_created_accrual(
    async_client: AsyncClient,
    admin_token: str,
    financial_subject_fixture: FinancialSubject,
    contribution_type_fixture: ContributionType,
    test_db,
) -> None:
    """Тест 400 при попытке применить уже применённое начисление."""
    subject = financial_subject_fixture
    ct = contribution_type_fixture

    # Создаём применённое начисление
    accrual = Accrual(
        financial_subject_id=subject.id,
        contribution_type_id=ct.id,
        amount=Decimal("1000.00"),
        accrual_date=date.today(),
        period_start=date.today().replace(month=1, day=1),
        status="applied",
    )
    test_db.add(accrual)
    await test_db.commit()

    # Пытаемся применить
    response = await async_client.post(
        f"/api/v1/accruals/{accrual.id}/apply",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_mass_create_accruals(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
    contribution_type_fixture: ContributionType,
) -> None:
    """Тест массового создания начислений."""
    # Создаём несколько финансовых субъектов
    coop = Cooperative(name="СТ Для массового")
    test_db.add(coop)
    await test_db.flush()

    subjects = []
    for i in range(3):
        plot = LandPlot(
            cooperative_id=coop.id, plot_number=f"Массовый {i}", area_sqm=Decimal("500.00")
        )
        test_db.add(plot)
        await test_db.flush()

        subject = FinancialSubject(
            subject_type="LAND_PLOT",
            subject_id=plot.id,
            cooperative_id=coop.id,
        )
        test_db.add(subject)
        subjects.append(subject)

    await test_db.commit()

    ct = contribution_type_fixture

    accruals_data = {
        "accruals": [
            {
                "financial_subject_id": str(s.id),
                "contribution_type_id": str(ct.id),
                "amount": "500.00",
                "accrual_date": str(date.today()),
                "period_start": str(date.today().replace(month=1, day=1)),
                "period_end": str(date.today().replace(month=12, day=31)),
            }
            for s in subjects
        ]
    }

    response = await async_client.post(
        "/api/v1/accruals/batch",
        json=accruals_data,
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert len(data) == 3
    assert all(a["status"] == "created" for a in data)


@pytest.mark.asyncio
async def test_get_accruals_by_financial_subject(
    async_client: AsyncClient,
    admin_token: str,
    financial_subject_fixture: FinancialSubject,
    contribution_type_fixture: ContributionType,
    test_db,
) -> None:
    """Тест получения начислений по финансовому субъекту."""
    subject = financial_subject_fixture
    ct = contribution_type_fixture

    # Создаём несколько начислений
    for amount in [Decimal("100.00"), Decimal("200.00"), Decimal("300.00")]:
        accrual = Accrual(
            financial_subject_id=subject.id,
            contribution_type_id=ct.id,
            amount=amount,
            accrual_date=date.today(),
            period_start=date.today().replace(month=1, day=1),
            status="applied",
        )
        test_db.add(accrual)

    await test_db.commit()

    response = await async_client.get(
        "/api/v1/accruals/",
        params={"financial_subject_id": str(subject.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_get_accruals_by_cooperative(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
    contribution_type_fixture: ContributionType,
) -> None:
    """Тест получения начислений по СТ."""
    coop = Cooperative(name="СТ Для списка")
    test_db.add(coop)
    await test_db.flush()

    plot = LandPlot(cooperative_id=coop.id, plot_number="Список", area_sqm=Decimal("500.00"))
    test_db.add(plot)
    await test_db.flush()

    subject = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=plot.id,
        cooperative_id=coop.id,
    )
    test_db.add(subject)
    await test_db.flush()

    ct = contribution_type_fixture

    accrual = Accrual(
        financial_subject_id=subject.id,
        contribution_type_id=ct.id,
        amount=Decimal("1000.00"),
        accrual_date=date.today(),
        period_start=date.today().replace(month=1, day=1),
        status="applied",
    )
    test_db.add(accrual)
    await test_db.commit()

    response = await async_client.get(
        "/api/v1/accruals/",
        params={"cooperative_id": str(coop.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_create_accrual_forbidden_for_other_cooperative(
    async_client: AsyncClient,
    treasurer_token: str,
    test_db,
    contribution_type_fixture: ContributionType,
) -> None:
    """Тест 403 при попытке создать начисление для чужого СТ."""
    # Создаём другое СТ
    other_coop = Cooperative(name="Чужое СТ")
    test_db.add(other_coop)
    await test_db.flush()

    plot = LandPlot(cooperative_id=other_coop.id, plot_number="Чужой", area_sqm=Decimal("500.00"))
    test_db.add(plot)
    await test_db.flush()

    subject = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=plot.id,
        cooperative_id=other_coop.id,
    )
    test_db.add(subject)
    await test_db.commit()

    ct = contribution_type_fixture

    response = await async_client.post(
        "/api/v1/accruals/",
        json={
            "financial_subject_id": str(subject.id),
            "contribution_type_id": str(ct.id),
            "amount": "1000.00",
            "accrual_date": str(date.today()),
            "period_start": str(date.today().replace(month=1, day=1)),
        },
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_accrual_missing_params(
    async_client: AsyncClient,
    admin_token: str,
) -> None:
    """Тест 400 при отсутствии financial_subject_id или cooperative_id."""
    response = await async_client.get(
        "/api/v1/accruals/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400
