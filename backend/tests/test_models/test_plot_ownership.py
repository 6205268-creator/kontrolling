from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cooperative_core.infrastructure.models import CooperativeModel as Cooperative
from app.modules.land_management.infrastructure.models import LandPlotModel as LandPlot
from app.modules.land_management.infrastructure.models import OwnerModel as Owner
from app.modules.land_management.infrastructure.models import PlotOwnershipModel as PlotOwnership


async def _make_coop_plot_owner(test_db: AsyncSession):
    """Фикстура-хелпер: Cooperative, LandPlot, Owner."""
    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()
    plot = LandPlot(cooperative_id=coop.id, plot_number="1", area_sqm=500)
    test_db.add(plot)
    await test_db.flush()
    owner = Owner(owner_type="physical", name="Иванов Иван")
    test_db.add(owner)
    await test_db.flush()
    return coop, plot, owner


@pytest.mark.asyncio
async def test_create_plot_ownership_full_share(test_db: AsyncSession) -> None:
    """Создание PlotOwnership с долей 1/1."""
    _, plot, owner = await _make_coop_plot_owner(test_db)

    po = PlotOwnership(
        land_plot_id=plot.id,
        owner_id=owner.id,
        share_numerator=1,
        share_denominator=1,
        is_primary=True,
        valid_from=date(2024, 1, 1),
    )
    test_db.add(po)
    await test_db.commit()
    await test_db.refresh(po)

    assert po.id is not None
    assert po.share_numerator == 1
    assert po.share_denominator == 1
    assert po.is_primary is True
    assert po.valid_from == date(2024, 1, 1)
    assert po.valid_to is None


@pytest.mark.asyncio
async def test_plot_ownership_two_owners_half_share(test_db: AsyncSession) -> None:
    """Несколько владельцев с долями 1/2, 1/2."""
    _, plot, owner1 = await _make_coop_plot_owner(test_db)
    owner2 = Owner(owner_type="physical", name="Петров Пётр")
    test_db.add(owner2)
    await test_db.flush()

    po1 = PlotOwnership(
        land_plot_id=plot.id,
        owner_id=owner1.id,
        share_numerator=1,
        share_denominator=2,
        is_primary=True,
        valid_from=date(2024, 1, 1),
    )
    po2 = PlotOwnership(
        land_plot_id=plot.id,
        owner_id=owner2.id,
        share_numerator=1,
        share_denominator=2,
        is_primary=False,
        valid_from=date(2024, 1, 1),
    )
    test_db.add_all([po1, po2])
    await test_db.commit()

    await test_db.refresh(po1)
    await test_db.refresh(po2)
    assert po1.share_numerator == 1 and po1.share_denominator == 2
    assert po2.share_numerator == 1 and po2.share_denominator == 2
    assert po1.is_primary is True
    assert po2.is_primary is False


@pytest.mark.asyncio
async def test_plot_ownership_share_constraint(test_db: AsyncSession) -> None:
    """Check constraint: share_numerator <= share_denominator."""
    _, plot, owner = await _make_coop_plot_owner(test_db)

    po = PlotOwnership(
        land_plot_id=plot.id,
        owner_id=owner.id,
        share_numerator=3,
        share_denominator=2,
        is_primary=True,
        valid_from=date(2024, 1, 1),
    )
    test_db.add(po)
    with pytest.raises(IntegrityError):
        await test_db.commit()
    await test_db.rollback()


@pytest.mark.asyncio
async def test_plot_ownership_primary_retrieval(test_db: AsyncSession) -> None:
    """Проверка is_primary: один primary на участок — выборка по участку возвращает его."""
    _, plot, owner = await _make_coop_plot_owner(test_db)

    po = PlotOwnership(
        land_plot_id=plot.id,
        owner_id=owner.id,
        share_numerator=1,
        share_denominator=1,
        is_primary=True,
        valid_from=date(2024, 1, 1),
    )
    test_db.add(po)
    await test_db.commit()

    from sqlalchemy import select

    result = await test_db.execute(
        select(PlotOwnership).where(
            PlotOwnership.land_plot_id == plot.id,
            PlotOwnership.is_primary.is_(True),
        )
    )
    primary_list = result.scalars().all()
    assert len(primary_list) == 1
    assert primary_list[0].owner_id == owner.id
    assert primary_list[0].is_primary is True
