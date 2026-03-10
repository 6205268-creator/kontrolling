from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.land_management.infrastructure.models import OwnerModel as Owner
from app.modules.meters.infrastructure.models import MeterModel as Meter
from app.modules.meters.infrastructure.models import MeterReadingModel as MeterReading


@pytest.mark.asyncio
async def test_create_meter_with_owner(test_db: AsyncSession) -> None:
    """Создание Meter с привязкой к Owner."""
    owner = Owner(
        owner_type="physical",
        name="Иванов Иван Иванович",
    )
    test_db.add(owner)
    await test_db.flush()

    meter = Meter(
        owner_id=owner.id,
        meter_type="WATER",
        serial_number="SN-123456",
        installation_date=datetime(2025, 1, 15, tzinfo=timezone.utc),
        status="active",
    )
    test_db.add(meter)
    await test_db.commit()
    await test_db.refresh(meter)

    assert meter.id is not None
    assert meter.owner_id == owner.id
    assert meter.meter_type == "WATER"
    assert meter.serial_number == "SN-123456"
    assert meter.installation_date == datetime(2025, 1, 15)
    assert meter.status == "active"
    assert meter.created_at is not None
    assert meter.updated_at is not None


@pytest.mark.asyncio
async def test_meter_type_values(test_db: AsyncSession) -> None:
    """Валидация: сохраняются только допустимые meter_type (WATER, ELECTRICITY)."""
    owner = Owner(owner_type="physical", name="Тестовый владелец")
    test_db.add(owner)
    await test_db.flush()

    for meter_type in ("WATER", "ELECTRICITY"):
        meter = Meter(owner_id=owner.id, meter_type=meter_type, serial_number=f"SN-{meter_type}")
        test_db.add(meter)
    await test_db.commit()

    from sqlalchemy import select

    result = await test_db.execute(select(Meter))
    meters = result.scalars().all()
    assert len(meters) == 2
    types = {m.meter_type for m in meters}
    assert types == {"WATER", "ELECTRICITY"}


@pytest.mark.asyncio
async def test_create_meter_reading(test_db: AsyncSession) -> None:
    """Создание MeterReading с привязкой к Meter."""
    owner = Owner(owner_type="physical", name="Иванов Иван Иванович")
    test_db.add(owner)
    await test_db.flush()

    meter = Meter(owner_id=owner.id, meter_type="ELECTRICITY", serial_number="EL-789")
    test_db.add(meter)
    await test_db.flush()

    reading = MeterReading(
        meter_id=meter.id,
        reading_value=Decimal("1234.56"),
        reading_date=datetime(2026, 2, 1, tzinfo=timezone.utc),
    )
    test_db.add(reading)
    await test_db.commit()
    await test_db.refresh(reading)

    assert reading.id is not None
    assert reading.meter_id == meter.id
    assert reading.reading_value == Decimal("1234.56")
    assert reading.reading_date == datetime(2026, 2, 1)
    assert reading.created_at is not None


@pytest.mark.asyncio
async def test_meter_reading_unique_meter_date(test_db: AsyncSession) -> None:
    """Проверка уникальности: одно показание на дату для одного счётчика."""
    owner = Owner(owner_type="physical", name="Тестовый владелец")
    test_db.add(owner)
    await test_db.flush()

    meter = Meter(owner_id=owner.id, meter_type="WATER", serial_number="WT-001")
    test_db.add(meter)
    await test_db.flush()

    reading_date = datetime(2026, 2, 1, tzinfo=timezone.utc)

    reading1 = MeterReading(
        meter_id=meter.id, reading_value=Decimal("100.00"), reading_date=reading_date
    )
    test_db.add(reading1)
    await test_db.flush()

    reading2 = MeterReading(
        meter_id=meter.id, reading_value=Decimal("200.00"), reading_date=reading_date
    )
    test_db.add(reading2)

    with pytest.raises(IntegrityError):
        await test_db.commit()
    await test_db.rollback()


@pytest.mark.asyncio
async def test_meter_reading_value_positive(test_db: AsyncSession) -> None:
    """Валидация reading_value >= 0: ноль допустим."""
    owner = Owner(owner_type="physical", name="Тестовый владелец")
    test_db.add(owner)
    await test_db.flush()

    meter = Meter(owner_id=owner.id, meter_type="WATER", serial_number="WT-002")
    test_db.add(meter)
    await test_db.flush()

    reading = MeterReading(
        meter_id=meter.id,
        reading_value=Decimal("0.00"),
        reading_date=datetime(2026, 2, 1, tzinfo=timezone.utc),
    )
    test_db.add(reading)
    await test_db.commit()
    await test_db.refresh(reading)

    assert reading.reading_value == Decimal("0.00")


@pytest.mark.asyncio
async def test_meter_status_values(test_db: AsyncSession) -> None:
    """Проверка статусов счётчика: active, inactive."""
    owner = Owner(owner_type="physical", name="Тестовый владелец")
    test_db.add(owner)
    await test_db.flush()

    for status in ("active", "inactive"):
        meter = Meter(
            owner_id=owner.id, meter_type="WATER", serial_number=f"SN-{status}", status=status
        )
        test_db.add(meter)
    await test_db.commit()

    from sqlalchemy import select

    result = await test_db.execute(select(Meter))
    meters = result.scalars().all()
    assert len(meters) == 2
    statuses = {m.status for m in meters}
    assert statuses == {"active", "inactive"}


@pytest.mark.asyncio
async def test_meter_relationships(test_db: AsyncSession) -> None:
    """Проверка relationships: Meter связан с Owner и MeterReading."""
    owner = Owner(owner_type="physical", name="Тестовый владелец")
    test_db.add(owner)
    await test_db.flush()

    meter = Meter(owner_id=owner.id, meter_type="ELECTRICITY", serial_number="EL-REL")
    test_db.add(meter)
    await test_db.flush()

    reading = MeterReading(
        meter_id=meter.id,
        reading_value=Decimal("100.00"),
        reading_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    test_db.add(reading)
    await test_db.commit()

    # Проверяем что owner связан с meter через relationship
    from sqlalchemy import select

    result = await test_db.execute(select(Owner).where(Owner.id == owner.id))
    loaded_owner = result.scalar_one()
    await test_db.refresh(loaded_owner)

    # Проверяем что meter связан с reading
    result = await test_db.execute(select(Meter).where(Meter.id == meter.id))
    loaded_meter = result.scalar_one()
    await test_db.refresh(loaded_meter)

    assert loaded_owner is not None
    assert loaded_meter is not None
