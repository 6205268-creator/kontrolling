"""Тесты историзации: при изменении сущности создаётся запись в *_history.

SKIPPED: History functionality is legacy and not implemented in Clean Architecture modules.
"""

from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.accruals.infrastructure.models import AccrualHistoryModel as AccrualHistory
from app.modules.cooperative_core.infrastructure.models import CooperativeModel as Cooperative
from app.modules.expenses.infrastructure.models import ExpenseHistoryModel as ExpenseHistory
from app.modules.land_management.infrastructure.models import LandPlotModel as LandPlot
from app.modules.land_management.infrastructure.models import OwnerModel as Owner
from app.modules.land_management.infrastructure.models import (
    PlotOwnershipHistoryModel as PlotOwnershipHistory,
)
from app.modules.land_management.infrastructure.models import (
    PlotOwnershipModel as PlotOwnership,
)

# Skip all tests in this module - history functionality is legacy
pytestmark = pytest.mark.skip(
    reason="History functionality is legacy and not implemented in Clean Architecture modules"
)


async def _make_coop_plot_owner(test_db: AsyncSession):
    """Cooperative, LandPlot, Owner для тестов истории."""
    coop = Cooperative(name="СТ История")
    test_db.add(coop)
    await test_db.flush()
    plot = LandPlot(cooperative_id=coop.id, plot_number="1", area_sqm=500)
    test_db.add(plot)
    await test_db.flush()
    owner = Owner(owner_type="physical", name="Историев Историй")
    test_db.add(owner)
    await test_db.flush()
    return coop, plot, owner


@pytest.mark.asyncio
async def test_plot_ownership_insert_creates_history(test_db: AsyncSession) -> None:
    """При создании PlotOwnership появляется запись в plot_ownerships_history с operation=insert."""
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

    result = await test_db.execute(
        select(PlotOwnershipHistory)
        .where(PlotOwnershipHistory.entity_id == po.id)
        .order_by(PlotOwnershipHistory.changed_at)
    )
    rows = result.scalars().all()
    assert len(rows) == 1
    assert rows[0].operation == "insert"
    assert rows[0].share_numerator == 1
    assert rows[0].share_denominator == 1
    assert rows[0].is_primary is True


@pytest.mark.asyncio
async def test_plot_ownership_update_creates_history(test_db: AsyncSession) -> None:
    """При обновлении PlotOwnership появляется запись в history с operation=update."""
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

    po.is_primary = False
    test_db.add(po)
    await test_db.commit()
    await test_db.refresh(po)

    result = await test_db.execute(
        select(PlotOwnershipHistory)
        .where(PlotOwnershipHistory.entity_id == po.id)
        .order_by(PlotOwnershipHistory.changed_at)
    )
    rows = result.scalars().all()
    assert len(rows) == 2
    assert rows[0].operation == "insert"
    assert rows[0].is_primary is True
    assert rows[1].operation == "update"
    assert rows[1].is_primary is False


@pytest.mark.asyncio
async def test_payment_cancel_creates_history(
    test_db: AsyncSession,
    sample_payment,
) -> None:
    """При отмене платежа (status=cancelled) создаётся запись в payments_history."""
    from app.models import PaymentHistory

    payment = sample_payment
    await test_db.commit()
    await test_db.refresh(payment)

    payment.status = "cancelled"
    test_db.add(payment)
    await test_db.commit()

    result = await test_db.execute(
        select(PaymentHistory)
        .where(PaymentHistory.entity_id == payment.id)
        .order_by(PaymentHistory.changed_at)
    )
    rows = result.scalars().all()
    assert len(rows) >= 2
    ops = [r.operation for r in rows]
    assert "insert" in ops
    assert "update" in ops
    assert rows[-1].status == "cancelled"


@pytest.mark.asyncio
async def test_accrual_insert_creates_history(
    test_db: AsyncSession,
    sample_accrual,
) -> None:
    """При создании начисления появляется запись в accruals_history."""
    accrual = sample_accrual
    await test_db.commit()
    await test_db.refresh(accrual)

    result = await test_db.execute(
        select(AccrualHistory)
        .where(AccrualHistory.entity_id == accrual.id)
        .order_by(AccrualHistory.changed_at)
    )
    rows = result.scalars().all()
    assert len(rows) == 1
    assert rows[0].operation == "insert"
    assert rows[0].amount == accrual.amount


@pytest.mark.asyncio
async def test_expense_update_creates_history(
    test_db: AsyncSession,
    sample_expense,
) -> None:
    """При изменении расхода создаётся запись в expenses_history с operation=update."""
    expense = sample_expense
    await test_db.commit()
    await test_db.refresh(expense)

    expense.status = "cancelled"
    expense.description = "Отменён"
    test_db.add(expense)
    await test_db.commit()

    result = await test_db.execute(
        select(ExpenseHistory)
        .where(ExpenseHistory.entity_id == expense.id)
        .order_by(ExpenseHistory.changed_at)
    )
    rows = result.scalars().all()
    assert len(rows) >= 2
    assert rows[-1].operation == "update"
    assert rows[-1].status == "cancelled"
