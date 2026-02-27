import uuid
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.cooperative import Cooperative
from app.models.land_plot import LandPlot


@pytest.mark.asyncio
async def test_land_plot_via_fixture(sample_land_plot: LandPlot, sample_cooperative: Cooperative) -> None:
    """Фикстуры sample_land_plot и sample_cooperative создают связанные сущности без дублирования кода."""
    assert sample_land_plot.id is not None
    assert sample_land_plot.cooperative_id == sample_cooperative.id
    assert sample_land_plot.plot_number == "1"
    assert sample_land_plot.area_sqm == Decimal("600.00")


@pytest.mark.asyncio
async def test_create_land_plot_with_cooperative(test_db: AsyncSession) -> None:
    """Создание LandPlot с привязкой к Cooperative."""
    coop = Cooperative(name="СТ Ромашка")
    test_db.add(coop)
    await test_db.flush()

    plot = LandPlot(
        cooperative_id=coop.id,
        plot_number="42",
        area_sqm=Decimal("600.00"),
        cadastral_number="12345",
        status="active",
    )
    test_db.add(plot)
    await test_db.commit()
    await test_db.refresh(plot)

    assert plot.id is not None
    assert isinstance(plot.id, uuid.UUID)
    assert plot.cooperative_id == coop.id
    assert plot.plot_number == "42"
    assert plot.area_sqm == Decimal("600.00")
    assert plot.cadastral_number == "12345"
    assert plot.status == "active"
    assert plot.created_at is not None
    assert plot.updated_at is not None


@pytest.mark.asyncio
async def test_land_plot_plot_number_unique_per_cooperative(test_db: AsyncSession) -> None:
    """Уникальность plot_number в рамках одного СТ; в другом СТ тот же номер допустим."""
    coop1 = Cooperative(name="СТ Первое")
    coop2 = Cooperative(name="СТ Второе")
    test_db.add_all([coop1, coop2])
    await test_db.flush()

    plot1 = LandPlot(cooperative_id=coop1.id, plot_number="1", area_sqm=Decimal("500"))
    test_db.add(plot1)
    await test_db.commit()

    coop2_id = coop2.id
    plot2_same_coop = LandPlot(cooperative_id=coop1.id, plot_number="1", area_sqm=Decimal("600"))
    test_db.add(plot2_same_coop)
    with pytest.raises(IntegrityError):
        await test_db.commit()
    await test_db.rollback()

    plot2_other_coop = LandPlot(cooperative_id=coop2_id, plot_number="1", area_sqm=Decimal("600"))
    test_db.add(plot2_other_coop)
    await test_db.commit()
    await test_db.refresh(plot2_other_coop)
    assert plot2_other_coop.plot_number == "1"
    assert plot2_other_coop.cooperative_id == coop2_id


@pytest.mark.asyncio
async def test_land_plot_status_values(test_db: AsyncSession) -> None:
    """Валидация статуса: active, vacant, archived."""
    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    for status in ("active", "vacant", "archived"):
        plot = LandPlot(
            cooperative_id=coop.id,
            plot_number=f"plot_{status}",
            area_sqm=Decimal("100"),
            status=status,
        )
        test_db.add(plot)
    await test_db.commit()

    from sqlalchemy import select
    result = await test_db.execute(select(LandPlot).where(LandPlot.cooperative_id == coop.id))
    plots = result.scalars().all()
    assert len(plots) == 3
    statuses = {p.status for p in plots}
    assert statuses == {"active", "vacant", "archived"}


@pytest.mark.asyncio
async def test_land_plot_default_status(test_db: AsyncSession) -> None:
    """По умолчанию status = active."""
    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()
    plot = LandPlot(cooperative_id=coop.id, plot_number="99", area_sqm=Decimal("200"))
    test_db.add(plot)
    await test_db.commit()
    await test_db.refresh(plot)
    assert plot.status == "active"
