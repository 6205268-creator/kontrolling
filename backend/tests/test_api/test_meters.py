from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import create_access_token, get_password_hash

# Import models from Clean Architecture modules
from app.modules.administration.infrastructure.models import AppUserModel as AppUser
from app.modules.cooperative_core.infrastructure.models import CooperativeModel as Cooperative
from app.modules.land_management.infrastructure.models import OwnerModel as Owner
from app.modules.meters.infrastructure.models import MeterModel as Meter
from app.modules.meters.infrastructure.models import MeterReadingModel as MeterReading


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
async def owner_with_plot_fixture(test_db) -> Owner:
    """Создаёт владельца с участком для счётчиков."""
    coop = Cooperative(name="СТ Для владельца")
    test_db.add(coop)
    await test_db.flush()

    owner = Owner(
        owner_type="physical",
        name="Владелец Тест",
        tax_id="123456",
    )
    test_db.add(owner)
    await test_db.flush()

    # Создаём участок для владельца
    from datetime import date

    from app.modules.land_management.infrastructure.models import LandPlotModel as LandPlot
    from app.modules.land_management.infrastructure.models import (
        PlotOwnershipModel as PlotOwnership,
    )

    plot = LandPlot(
        cooperative_id=coop.id,
        plot_number="Тестовый",
        area_sqm=Decimal("600.00"),
    )
    test_db.add(plot)
    await test_db.flush()

    # Создаём право собственности
    ownership = PlotOwnership(
        land_plot_id=plot.id,
        owner_id=owner.id,
        share_numerator=1,
        share_denominator=1,
        is_primary=True,
        valid_from=date.today(),
    )
    test_db.add(ownership)
    await test_db.commit()

    return owner


@pytest.mark.asyncio
async def test_create_meter_water(
    async_client: AsyncClient,
    admin_token: str,
    owner_with_plot_fixture: Owner,
) -> None:
    """Тест создания счётчика воды."""
    owner = owner_with_plot_fixture

    response = await async_client.post(
        "/api/meters/",
        json={
            "owner_id": str(owner.id),
            "meter_type": "WATER",
            "serial_number": "W123456",
            "installation_date": str(datetime.now()),
            "status": "active",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["meter_type"] == "WATER"
    assert data["serial_number"] == "W123456"


@pytest.mark.asyncio
async def test_create_meter_electricity(
    async_client: AsyncClient,
    admin_token: str,
    owner_with_plot_fixture: Owner,
) -> None:
    """Тест создания счётчика электроэнергии."""
    owner = owner_with_plot_fixture

    response = await async_client.post(
        "/api/meters/",
        json={
            "owner_id": str(owner.id),
            "meter_type": "ELECTRICITY",
            "serial_number": "E789012",
            "status": "active",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["meter_type"] == "ELECTRICITY"


@pytest.mark.asyncio
async def test_create_meter_auto_creates_financial_subject(
    async_client: AsyncClient,
    admin_token: str,
    owner_with_plot_fixture: Owner,
    test_db,
) -> None:
    """Тест что при создании счётчика автоматически создаётся FinancialSubject."""
    owner = owner_with_plot_fixture

    response = await async_client.post(
        "/api/meters/",
        json={
            "owner_id": str(owner.id),
            "meter_type": "WATER",
            "serial_number": "W_TEST",
            "status": "active",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201

    # Проверяем что FinancialSubject создан
    from app.modules.financial_core.infrastructure.models import (
        FinancialSubjectModel as FinancialSubject,
    )

    meter_id = response.json()["id"]

    # Проверяем что владелец имеет участок
    from app.modules.land_management.infrastructure.models import LandPlotModel as LandPlot
    from app.modules.land_management.infrastructure.models import (
        PlotOwnershipModel as PlotOwnership,
    )

    ownership_result = await test_db.execute(
        select(PlotOwnership)
        .join(LandPlot, PlotOwnership.land_plot_id == LandPlot.id)
        .where(PlotOwnership.owner_id == owner.id)
    )
    ownership = ownership_result.scalar_one_or_none()

    # Если владелец имеет участок, FinancialSubject должен быть создан
    if ownership:
        result = await test_db.execute(
            select(FinancialSubject).where(
                FinancialSubject.subject_type == "WATER_METER",
                FinancialSubject.subject_id == meter_id,
            )
        )
        fs = result.scalar_one_or_none()
        assert fs is not None
        # Проверяем cooperative_id напрямую
        land_plot_result = await test_db.execute(
            select(LandPlot).where(LandPlot.id == ownership.land_plot_id)
        )
        land_plot = land_plot_result.scalar_one_or_none()
        assert fs.cooperative_id == land_plot.cooperative_id


@pytest.mark.asyncio
async def test_get_meters_by_owner(
    async_client: AsyncClient,
    admin_token: str,
    owner_with_plot_fixture: Owner,
    test_db,
) -> None:
    """Тест получения счётчиков владельца."""
    owner = owner_with_plot_fixture

    # Создаём несколько счётчиков
    for i, meter_type in enumerate(["WATER", "ELECTRICITY"]):
        meter = Meter(
            owner_id=owner.id,
            meter_type=meter_type,
            serial_number=f"METER_{i}",
            status="active",
        )
        test_db.add(meter)

    await test_db.commit()

    response = await async_client.get(
        "/api/meters/",
        params={"owner_id": str(owner.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_meter_by_id(
    async_client: AsyncClient,
    admin_token: str,
    owner_with_plot_fixture: Owner,
    test_db,
) -> None:
    """Тест получения счётчика по ID."""
    owner = owner_with_plot_fixture

    meter = Meter(
        owner_id=owner.id,
        meter_type="WATER",
        serial_number="W_GET",
        status="active",
    )
    test_db.add(meter)
    await test_db.commit()

    response = await async_client.get(
        f"/api/meters/{meter.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["serial_number"] == "W_GET"


@pytest.mark.asyncio
async def test_get_meter_not_found(
    async_client: AsyncClient,
    admin_token: str,
) -> None:
    """Тест получения несуществующего счётчика."""
    import uuid

    fake_id = uuid.uuid4()

    response = await async_client.get(
        f"/api/meters/{fake_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_meter_reading(
    async_client: AsyncClient,
    admin_token: str,
    owner_with_plot_fixture: Owner,
    test_db,
) -> None:
    """Тест добавления показания счётчика."""
    owner = owner_with_plot_fixture

    meter = Meter(
        owner_id=owner.id,
        meter_type="WATER",
        serial_number="W_READING",
        status="active",
    )
    test_db.add(meter)
    await test_db.commit()

    response = await async_client.post(
        f"/api/meters/{meter.id}/readings",
        json={
            "meter_id": str(meter.id),
            "reading_value": "125.500",
            "reading_date": str(datetime.now()),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert float(data["reading_value"]) == 125.5


@pytest.mark.asyncio
async def test_get_meter_readings(
    async_client: AsyncClient,
    admin_token: str,
    owner_with_plot_fixture: Owner,
    test_db,
) -> None:
    """Тест получения истории показаний."""
    owner = owner_with_plot_fixture

    meter = Meter(
        owner_id=owner.id,
        meter_type="WATER",
        serial_number="W_HISTORY",
        status="active",
    )
    test_db.add(meter)
    await test_db.flush()

    # Добавляем несколько показаний
    for i in range(3):
        reading = MeterReading(
            meter_id=meter.id,
            reading_value=Decimal(f"{100 + i * 10}.000"),
            reading_date=datetime.now() - timedelta(days=i * 30),
        )
        test_db.add(reading)

    await test_db.commit()

    response = await async_client.get(
        f"/api/meters/{meter.id}/readings",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_add_meter_reading_duplicate_date(
    async_client: AsyncClient,
    admin_token: str,
    owner_with_plot_fixture: Owner,
    test_db,
) -> None:
    """Тест 400 при добавлении показания на ту же дату."""
    owner = owner_with_plot_fixture

    meter = Meter(
        owner_id=owner.id,
        meter_type="WATER",
        serial_number="W_DUP",
        status="active",
    )
    test_db.add(meter)
    await test_db.flush()

    # Добавляем первое показание
    reading_date = datetime.now()
    reading = MeterReading(
        meter_id=meter.id,
        reading_value=Decimal("100.000"),
        reading_date=reading_date,
    )
    test_db.add(reading)
    await test_db.commit()

    # Пытаемся добавить второе на ту же дату
    response = await async_client.post(
        f"/api/meters/{meter.id}/readings",
        json={
            "meter_id": str(meter.id),
            "reading_value": "150.000",
            "reading_date": str(reading_date),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_meter_owner_not_found(
    async_client: AsyncClient,
    admin_token: str,
) -> None:
    """Тест 400 при создании счётчика с несуществующим владельцем."""
    import uuid

    response = await async_client.post(
        "/api/meters/",
        json={
            "owner_id": str(uuid.uuid4()),
            "meter_type": "WATER",
            "serial_number": "W_INVALID",
            "status": "active",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_meters_missing_owner_id(
    async_client: AsyncClient,
    admin_token: str,
) -> None:
    """Тест 400 при отсутствии owner_id."""
    response = await async_client.get(
        "/api/meters/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400
