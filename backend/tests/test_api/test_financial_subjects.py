from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, get_password_hash

# Import models from Clean Architecture modules
from app.modules.accruals.infrastructure.models import AccrualModel as Accrual, ContributionTypeModel as ContributionType
from app.modules.administration.infrastructure.models import AppUserModel as AppUser
from app.modules.cooperative_core.infrastructure.models import CooperativeModel as Cooperative
from app.modules.financial_core.infrastructure.models import FinancialSubjectModel as FinancialSubject
from app.modules.land_management.infrastructure.models import LandPlotModel as LandPlot, OwnerModel as Owner
from app.modules.payments.infrastructure.models import PaymentModel as Payment


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
async def financial_subject_fixture(test_db) -> FinancialSubject:
    """Создаёт финансовый субъект с начислениями и платежами."""
    coop = Cooperative(name="СТ Для баланса")
    test_db.add(coop)
    await test_db.flush()

    plot = LandPlot(
        cooperative_id=coop.id,
        plot_number="Баланс Тест",
        area_sqm=Decimal("600.00"),
    )
    test_db.add(plot)
    await test_db.flush()

    subject = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=plot.id,
        cooperative_id=coop.id,
    )
    test_db.add(subject)
    await test_db.flush()

    # Создаём вид взноса
    contribution_type = ContributionType(name="Членский", code="MEMBER")
    test_db.add(contribution_type)
    await test_db.flush()

    # Создаём начисление
    accrual = Accrual(
        financial_subject_id=subject.id,
        contribution_type_id=contribution_type.id,
        amount=Decimal("1000.00"),
        accrual_date=date.today(),
        period_start=date.today().replace(month=1, day=1),
        status="applied",
    )
    test_db.add(accrual)

    # Создаём владельца и платёж
    owner = Owner(owner_type="physical", name="Плательщик")
    test_db.add(owner)
    await test_db.flush()

    payment = Payment(
        financial_subject_id=subject.id,
        payer_owner_id=owner.id,
        amount=Decimal("600.00"),
        payment_date=date.today(),
        status="confirmed",
    )
    test_db.add(payment)
    await test_db.commit()

    return subject


@pytest.mark.asyncio
async def test_get_financial_subjects_list(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
) -> None:
    """Тест получения списка финансовых субъектов."""
    coop = Cooperative(name="СТ Для списка")
    test_db.add(coop)
    await test_db.flush()

    plot = LandPlot(cooperative_id=coop.id, plot_number="Тест", area_sqm=Decimal("500.00"))
    test_db.add(plot)
    await test_db.flush()

    subject = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=plot.id,
        cooperative_id=coop.id,
    )
    test_db.add(subject)
    await test_db.commit()

    response = await async_client.get(
        "/api/financial-subjects/",
        params={"cooperative_id": str(coop.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_financial_subject_balance(
    async_client: AsyncClient,
    admin_token: str,
    financial_subject_fixture: FinancialSubject,
) -> None:
    """Тест получения баланса финансового субъекта."""
    subject = financial_subject_fixture

    response = await async_client.get(
        f"/api/financial-subjects/{subject.id}/balance",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["financial_subject_id"] == str(subject.id)
    assert data["total_accruals"] == "1000.00"
    assert data["total_payments"] == "600.00"
    assert data["balance"] == "400.00"


@pytest.mark.asyncio
async def test_get_financial_subject_balance_not_found(
    async_client: AsyncClient,
    admin_token: str,
) -> None:
    """Тест получения баланса несуществующего субъекта."""
    import uuid

    fake_id = uuid.uuid4()

    response = await async_client.get(
        f"/api/financial-subjects/{fake_id}/balance",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_balances_by_cooperative(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
) -> None:
    """Тест получения балансов всех субъектов СТ."""
    coop = Cooperative(name="СТ Для балансов")
    test_db.add(coop)
    await test_db.flush()

    # Создаём несколько субъектов
    for i in range(3):
        plot = LandPlot(
            cooperative_id=coop.id, plot_number=f"Участок {i}", area_sqm=Decimal("500.00")
        )
        test_db.add(plot)
        await test_db.flush()

        subject = FinancialSubject(
            subject_type="LAND_PLOT",
            subject_id=plot.id,
            cooperative_id=coop.id,
            code=f"FS-TEST{i}",
        )
        test_db.add(subject)

    await test_db.commit()

    response = await async_client.get(
        "/api/financial-subjects/balances",
        params={"cooperative_id": str(coop.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_get_balances_by_cooperative_treasurer(
    async_client: AsyncClient,
    treasurer_token: str,
    test_db,
) -> None:
    """Тест что treasurer видит только балансы своего СТ."""
    # Получаем СТ казначея
    coop_response = await async_client.get(
        "/api/cooperatives/",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )
    coop_id = coop_response.json()[0]["id"]

    # Создаём финансовый субъект
    plot = LandPlot(cooperative_id=UUID(coop_id), plot_number="Тест", area_sqm=Decimal("500.00"))
    test_db.add(plot)
    await test_db.flush()

    subject = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=plot.id,
        cooperative_id=UUID(coop_id),
    )
    test_db.add(subject)
    await test_db.commit()

    response = await async_client.get(
        "/api/financial-subjects/balances",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@pytest.mark.asyncio
async def test_get_financial_subjects_no_cooperative_id(
    async_client: AsyncClient,
    treasurer_token: str,
) -> None:
    """Тест что treasurer без cooperative_id получает список своего СТ."""
    response = await async_client.get(
        "/api/financial-subjects/",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    # Для treasurer cooperative_id подставляется автоматически
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_balance_forbidden_for_other_cooperative(
    async_client: AsyncClient,
    treasurer_token: str,
    test_db,
) -> None:
    """Тест 403 при попытке получить баланс чужого СТ."""
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

    response = await async_client.get(
        f"/api/financial-subjects/{subject.id}/balance",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 403
