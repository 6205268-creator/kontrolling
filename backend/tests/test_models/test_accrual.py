from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.accruals.infrastructure.models import AccrualModel as Accrual
from app.modules.accruals.infrastructure.models import ContributionTypeModel as ContributionType
from app.modules.cooperative_core.infrastructure.models import CooperativeModel as Cooperative
from app.modules.financial_core.infrastructure.models import (
    FinancialSubjectModel as FinancialSubject,
)


@pytest.mark.asyncio
async def test_create_accrual_with_financial_subject(test_db: AsyncSession) -> None:
    """Создание Accrual с привязкой к FinancialSubject и ContributionType."""
    coop = Cooperative(name="СТ Ромашка")
    test_db.add(coop)
    await test_db.flush()

    fs = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=coop.id,  # для теста используем любой uuid
        cooperative_id=coop.id,
    )
    test_db.add(fs)
    await test_db.flush()

    ct = ContributionType(name="Членский взнос", code="membership")
    test_db.add(ct)
    await test_db.flush()

    accrual = Accrual(
        financial_subject_id=fs.id,
        contribution_type_id=ct.id,
        amount=Decimal("50.00"),
        accrual_date=date(2026, 1, 15),
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        status="created",
        operation_number="ACC-M-1",
    )
    test_db.add(accrual)
    await test_db.commit()
    await test_db.refresh(accrual)

    assert accrual.id is not None
    assert accrual.financial_subject_id == fs.id
    assert accrual.contribution_type_id == ct.id
    assert accrual.amount == Decimal("50.00")
    assert accrual.accrual_date == date(2026, 1, 15)
    assert accrual.period_start == date(2026, 1, 1)
    assert accrual.period_end == date(2026, 1, 31)
    assert accrual.status == "created"
    assert accrual.created_at is not None
    assert accrual.updated_at is not None


@pytest.mark.asyncio
async def test_accrual_statuses_created_applied_cancelled(test_db: AsyncSession) -> None:
    """Проверка статусов: created → applied → cancelled."""
    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    fs = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=coop.id,
        cooperative_id=coop.id,
    )
    ct = ContributionType(name="Целевой", code="target")
    test_db.add_all([fs, ct])
    await test_db.flush()

    accrual = Accrual(
        financial_subject_id=fs.id,
        contribution_type_id=ct.id,
        amount=Decimal("100.00"),
        accrual_date=date(2026, 2, 1),
        period_start=date(2026, 2, 1),
        status="created",
        operation_number="ACC-M-2",
    )
    test_db.add(accrual)
    await test_db.commit()
    await test_db.refresh(accrual)
    assert accrual.status == "created"
    accrual.status = "applied"
    await test_db.commit()
    await test_db.refresh(accrual)
    assert accrual.status == "applied"
    accrual.status = "cancelled"
    await test_db.commit()
    await test_db.refresh(accrual)
    assert accrual.status == "cancelled"


@pytest.mark.asyncio
async def test_accrual_amount_zero_allowed(test_db: AsyncSession) -> None:
    """Валидация amount >= 0: ноль допустим."""
    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    fs = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=coop.id,
        cooperative_id=coop.id,
    )
    ct = ContributionType(name="Членский", code="mem")
    test_db.add_all([fs, ct])
    await test_db.flush()

    accrual = Accrual(
        financial_subject_id=fs.id,
        contribution_type_id=ct.id,
        amount=Decimal("0.00"),
        accrual_date=date(2026, 1, 1),
        period_start=date(2026, 1, 1),
        status="created",
        operation_number="ACC-M-3",
    )
    test_db.add(accrual)
    await test_db.flush()


@pytest.mark.asyncio
async def test_accrual_amount_negative_rejected(test_db: AsyncSession) -> None:
    """Валидация amount >= 0: отрицательная сумма отклоняется БД."""
    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    fs = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=coop.id,
        cooperative_id=coop.id,
    )
    ct = ContributionType(name="Членский", code="mem2")
    test_db.add_all([fs, ct])
    await test_db.flush()

    accrual = Accrual(
        financial_subject_id=fs.id,
        contribution_type_id=ct.id,
        amount=Decimal("-10.00"),
        accrual_date=date(2026, 1, 1),
        period_start=date(2026, 1, 1),
        status="created",
        operation_number="ACC-M-4",
    )
    test_db.add(accrual)
    with pytest.raises(IntegrityError):
        await test_db.commit()
    await test_db.rollback()


@pytest.mark.asyncio
async def test_accrual_amount_immutable_on_update(test_db: AsyncSession) -> None:
    """Этап 4: amount не изменяется при update (immutability)."""
    from app.modules.accruals.domain.entities import Accrual as AccrualEntity
    from app.modules.accruals.infrastructure.repositories import AccrualRepository

    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    fs = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=coop.id,
        cooperative_id=coop.id,
    )
    ct = ContributionType(name="Тестовый", code="test")
    test_db.add_all([fs, ct])
    await test_db.flush()

    original_amount = Decimal("50.00")
    accrual_model = Accrual(
        financial_subject_id=fs.id,
        contribution_type_id=ct.id,
        amount=original_amount,
        accrual_date=date(2026, 1, 15),
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        status="created",
        operation_number="ACC-M-5",
    )
    test_db.add(accrual_model)
    await test_db.commit()
    await test_db.refresh(accrual_model)

    # Создаём domain entity с изменённым amount (не из сессии)
    entity = AccrualEntity(
        id=accrual_model.id,
        financial_subject_id=accrual_model.financial_subject_id,
        contribution_type_id=accrual_model.contribution_type_id,
        amount=Decimal("999.99"),  # Пытаемся изменить amount
        accrual_date=accrual_model.accrual_date,
        period_start=accrual_model.period_start,
        period_end=accrual_model.period_end,
        status=accrual_model.status,
        operation_number=accrual_model.operation_number,
    )

    repo = AccrualRepository(test_db)
    updated = await repo.update(entity)

    # amount должен остаться оригинальным (не обновляться в БД)
    assert updated.amount == original_amount, (
        "Amount should be immutable - not updated in repository"
    )
