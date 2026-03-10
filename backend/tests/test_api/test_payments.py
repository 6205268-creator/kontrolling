from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, get_password_hash

# Import models from Clean Architecture modules
from app.modules.administration.infrastructure.models import AppUserModel as AppUser
from app.modules.cooperative_core.infrastructure.models import CooperativeModel as Cooperative
from app.modules.financial_core.infrastructure.models import (
    FinancialSubjectModel as FinancialSubject,
)
from app.modules.land_management.infrastructure.models import (
    LandPlotModel as LandPlot,
)
from app.modules.land_management.infrastructure.models import (
    OwnerModel as Owner,
)
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
    """Создаёт финансовый субъект (участок)."""
    coop = Cooperative(name="СТ Для платежей")
    test_db.add(coop)
    await test_db.flush()

    plot = LandPlot(cooperative_id=coop.id, plot_number="Платежи Тест", area_sqm=Decimal("600.00"))
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


@pytest.fixture
async def owner_fixture(test_db) -> Owner:
    """Создаёт владельца для платежей."""
    owner = Owner(owner_type="physical", name="Плательщик Тест", tax_id="123456")
    test_db.add(owner)
    await test_db.commit()
    return owner


@pytest.mark.asyncio
async def test_register_payment(
    async_client: AsyncClient,
    admin_token: str,
    financial_subject_fixture: FinancialSubject,
    owner_fixture: Owner,
) -> None:
    """Тест регистрации платежа."""
    subject = financial_subject_fixture
    owner = owner_fixture

    response = await async_client.post(
        f"/api/payments/?cooperative_id={str(subject.cooperative_id)}",
        json={
            "financial_subject_id": str(subject.id),
            "payer_owner_id": str(owner.id),
            "amount": "1500.00",
            "payment_date": str(date.today()),
            "document_number": "ПКО-001",
            "description": "Оплата взносов",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == "1500.00"
    assert data["status"] == "confirmed"
    assert data["document_number"] == "ПКО-001"


@pytest.mark.asyncio
async def test_cancel_payment(
    async_client: AsyncClient,
    admin_token: str,
    financial_subject_fixture: FinancialSubject,
    owner_fixture: Owner,
    test_db,
) -> None:
    """Тест отмены платежа."""
    subject = financial_subject_fixture
    owner = owner_fixture

    # Создаём платёж
    payment = Payment(
        financial_subject_id=subject.id,
        payer_owner_id=owner.id,
        amount=Decimal("1000.00"),
        payment_date=date.today(),
        status="confirmed",
        operation_number="PAY-API-CANCEL",
    )
    test_db.add(payment)
    await test_db.commit()

    response = await async_client.post(
        f"/api/payments/{payment.id}/cancel?cooperative_id={str(subject.cooperative_id)}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_already_cancelled_payment(
    async_client: AsyncClient,
    admin_token: str,
    financial_subject_fixture: FinancialSubject,
    owner_fixture: Owner,
    test_db,
) -> None:
    """Тест 400 при попытке отменить уже отменённый платёж."""
    subject = financial_subject_fixture
    owner = owner_fixture

    # Создаём отменённый платёж
    payment = Payment(
        financial_subject_id=subject.id,
        payer_owner_id=owner.id,
        amount=Decimal("1000.00"),
        payment_date=date.today(),
        status="cancelled",
        operation_number="PAY-API-ALREADY-CANCELLED",
    )
    test_db.add(payment)
    await test_db.commit()

    response = await async_client.post(
        f"/api/payments/{payment.id}/cancel?cooperative_id={str(subject.cooperative_id)}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_payments_by_financial_subject(
    async_client: AsyncClient,
    admin_token: str,
    financial_subject_fixture: FinancialSubject,
    owner_fixture: Owner,
    test_db,
) -> None:
    """Тест получения платежей по финансовому субъекту."""
    subject = financial_subject_fixture
    owner = owner_fixture

    # Создаём несколько платежей
    for i, amount in enumerate([Decimal("100.00"), Decimal("200.00"), Decimal("300.00")]):
        payment = Payment(
            financial_subject_id=subject.id,
            payer_owner_id=owner.id,
            amount=amount,
            payment_date=date.today(),
            status="confirmed",
            operation_number=f"PAY-API-FS-{i}",
        )
        test_db.add(payment)

    await test_db.commit()

    response = await async_client.get(
        "/api/payments/",
        params={
            "financial_subject_id": str(subject.id),
            "cooperative_id": str(subject.cooperative_id),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_get_payments_by_owner(
    async_client: AsyncClient,
    admin_token: str,
    financial_subject_fixture: FinancialSubject,
    owner_fixture: Owner,
    test_db,
) -> None:
    """Тест получения платежей владельца."""
    subject = financial_subject_fixture
    owner = owner_fixture

    # Создаём платежи
    for i in range(3):
        payment = Payment(
            financial_subject_id=subject.id,
            payer_owner_id=owner.id,
            amount=Decimal(f"{(i + 1) * 100}.00"),
            payment_date=date.today(),
            status="confirmed",
            operation_number=f"PAY-API-OWNER-{i}",
        )
        test_db.add(payment)

    await test_db.commit()

    response = await async_client.get(
        "/api/payments/",
        params={
            "owner_id": str(owner.id),
            "cooperative_id": str(subject.cooperative_id),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_get_payments_by_cooperative(
    async_client: AsyncClient,
    admin_token: str,
    test_db,
    owner_fixture: Owner,
) -> None:
    """Тест получения платежей по СТ."""
    coop = Cooperative(name="СТ Для списка платежей")
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

    payment = Payment(
        financial_subject_id=subject.id,
        payer_owner_id=owner_fixture.id,
        amount=Decimal("1000.00"),
        payment_date=date.today(),
        status="confirmed",
        operation_number="PAY-API-PAGINATION",
    )
    test_db.add(payment)
    await test_db.commit()

    response = await async_client.get(
        "/api/payments/",
        params={"cooperative_id": str(coop.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_create_payment_forbidden_for_other_cooperative(
    async_client: AsyncClient,
    treasurer_token: str,
    test_db,
    owner_fixture: Owner,
) -> None:
    """Тест 403 при попытке создать платёж для чужого СТ."""
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

    response = await async_client.post(
        f"/api/payments/?cooperative_id={str(other_coop.id)}",
        json={
            "financial_subject_id": str(subject.id),
            "payer_owner_id": str(owner_fixture.id),
            "amount": "1000.00",
            "payment_date": str(date.today()),
        },
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_payment_missing_params(
    async_client: AsyncClient,
    admin_token: str,
) -> None:
    """Тест 400 при отсутствии параметров фильтра."""
    response = await async_client.get(
        "/api/payments/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_payment_invalid_amount(
    async_client: AsyncClient,
    admin_token: str,
    financial_subject_fixture: FinancialSubject,
    owner_fixture: Owner,
) -> None:
    """Тест 422 при сумме <= 0."""
    subject = financial_subject_fixture
    owner = owner_fixture

    response = await async_client.post(
        "/api/payments/",
        json={
            "financial_subject_id": str(subject.id),
            "payer_owner_id": str(owner.id),
            "amount": "0.00",  # Неvalid
            "payment_date": str(date.today()),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_payments_treasurer_own_cooperative(
    async_client: AsyncClient,
    treasurer_token: str,
    test_db,
    owner_fixture: Owner,
) -> None:
    """Тест что treasurer видит только платежи своего СТ."""
    # Получаем СТ казначея
    coop_response = await async_client.get(
        "/api/cooperatives/",
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )
    coop_id = coop_response.json()[0]["id"]

    # Создаём платёж
    plot = LandPlot(cooperative_id=UUID(coop_id), plot_number="Тест", area_sqm=Decimal("500.00"))
    test_db.add(plot)
    await test_db.flush()

    subject = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=plot.id,
        cooperative_id=coop_id,
    )
    test_db.add(subject)
    await test_db.flush()

    payment = Payment(
        financial_subject_id=subject.id,
        payer_owner_id=owner_fixture.id,
        amount=Decimal("500.00"),
        payment_date=date.today(),
        status="confirmed",
        operation_number="PAY-API-FILTER",
    )
    test_db.add(payment)
    await test_db.commit()

    response = await async_client.get(
        "/api/payments/",
        params={"cooperative_id": coop_id},
        headers={"Authorization": f"Bearer {treasurer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
