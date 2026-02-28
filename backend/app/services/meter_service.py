from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financial_subject import FinancialSubject
from app.models.meter import Meter
from app.models.meter_reading import MeterReading
from app.schemas.meter import MeterCreate, MeterReadingCreate, MeterUpdate


async def create_meter(db: AsyncSession, meter_data: MeterCreate) -> Meter:
    """
    Создание счётчика.

    При создании счётчика автоматически создаётся FinancialSubject
    с типом WATER_METER или ELECTRICITY_METER.
    """
    # Получаем владельца для определения cooperative_id
    from app.models.financial_subject import FinancialSubject
    from app.models.owner import Owner
    from app.models.plot_ownership import PlotOwnership

    owner_result = await db.execute(select(Owner).where(Owner.id == meter_data.owner_id))
    owner = owner_result.scalar_one_or_none()
    if owner is None:
        raise ValueError(f"Owner {meter_data.owner_id} not found")

    # Получаем cooperative_id через PlotOwnership или Payment
    cooperative_id = None

    # Пробуем получить через PlotOwnership
    plot_ownership_result = await db.execute(
        select(PlotOwnership).where(PlotOwnership.owner_id == meter_data.owner_id).limit(1)
    )
    plot_ownership = plot_ownership_result.scalar_one_or_none()
    if plot_ownership:
        # Получаем участок чтобы узнать cooperative_id
        from app.models.land_plot import LandPlot

        land_plot_result = await db.execute(
            select(LandPlot).where(LandPlot.id == plot_ownership.land_plot_id)
        )
        land_plot = land_plot_result.scalar_one_or_none()
        if land_plot:
            cooperative_id = land_plot.cooperative_id

    # Если не нашли через PlotOwnership, пробуем через Payment
    if cooperative_id is None:
        from app.models.payment import Payment

        payment_result = await db.execute(
            select(Payment)
            .join(FinancialSubject, Payment.financial_subject_id == FinancialSubject.id)
            .where(Payment.payer_owner_id == meter_data.owner_id)
            .limit(1)
        )
        payment = payment_result.scalar_one_or_none()
        if payment and payment.financial_subject:
            cooperative_id = payment.financial_subject.cooperative_id

    # Если cooperative_id не найден, создаём счётчик без FinancialSubject
    # (пользователь должен сначала создать участок или платёж)

    # Создаём счётчик
    db_meter = Meter(
        owner_id=meter_data.owner_id,
        meter_type=meter_data.meter_type,
        serial_number=meter_data.serial_number,
        installation_date=meter_data.installation_date,
        status=meter_data.status,
    )
    db.add(db_meter)
    await db.flush()  # Получаем ID счётчика

    # Создаём финансовый субъект если cooperative_id найден
    if cooperative_id:
        # Определяем тип финансового субъекта
        subject_type = "WATER_METER" if meter_data.meter_type == "WATER" else "ELECTRICITY_METER"

        financial_subject = FinancialSubject(
            subject_type=subject_type,
            subject_id=db_meter.id,
            cooperative_id=cooperative_id,
        )
        db.add(financial_subject)

    await db.commit()
    await db.refresh(db_meter)
    return db_meter


async def get_meter(db: AsyncSession, meter_id: UUID) -> Meter | None:
    """Получение счётчика по ID."""
    result = await db.execute(select(Meter).where(Meter.id == meter_id))
    return result.scalar_one_or_none()


async def get_meters_by_owner(db: AsyncSession, owner_id: UUID) -> list[Meter]:
    """Получение списка счётчиков владельца."""
    result = await db.execute(
        select(Meter).where(Meter.owner_id == owner_id).order_by(Meter.created_at.desc())
    )
    return list(result.scalars().all())


async def update_meter(db: AsyncSession, meter_id: UUID, data: MeterUpdate) -> Meter | None:
    """Обновление счётчика."""
    meter = await get_meter(db, meter_id)
    if meter is None:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(meter, field, value)

    await db.commit()
    await db.refresh(meter)
    return meter


async def delete_meter(db: AsyncSession, meter_id: UUID) -> bool:
    """Удаление счётчика. Возвращает True если удалено."""
    meter = await get_meter(db, meter_id)
    if meter is None:
        return False

    await db.delete(meter)
    await db.commit()
    return True


async def add_meter_reading(db: AsyncSession, reading_data: MeterReadingCreate) -> MeterReading:
    """Добавление показания счётчика."""
    db_reading = MeterReading(
        meter_id=reading_data.meter_id,
        reading_value=reading_data.reading_value,
        reading_date=reading_data.reading_date,
    )
    db.add(db_reading)
    await db.commit()
    await db.refresh(db_reading)
    return db_reading


async def get_meter_readings(db: AsyncSession, meter_id: UUID) -> list[MeterReading]:
    """Получение истории показаний счётчика."""
    result = await db.execute(
        select(MeterReading)
        .where(MeterReading.meter_id == meter_id)
        .order_by(MeterReading.reading_date.desc())
    )
    return list(result.scalars().all())


async def get_meter_with_financial_subject(db: AsyncSession, meter_id: UUID) -> dict | None:
    """Получение счётчика с финансовым субъектом."""
    meter = await get_meter(db, meter_id)
    if meter is None:
        return None

    # Получаем финансовый субъект
    subject_type = "WATER_METER" if meter.meter_type == "WATER" else "ELECTRICITY_METER"
    fs_result = await db.execute(
        select(FinancialSubject).where(
            FinancialSubject.subject_type == subject_type,
            FinancialSubject.subject_id == meter_id,
        )
    )
    financial_subject = fs_result.scalar_one_or_none()

    return {
        "meter": meter,
        "financial_subject": financial_subject,
    }
