from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cooperative import Cooperative
from app.models.financial_subject import FinancialSubject
from app.models.owner import Owner
from app.models.payment import Payment


@pytest.mark.asyncio
async def test_create_payment_with_financial_subject_and_owner(test_db: AsyncSession) -> None:
    """Создание Payment с привязкой к FinancialSubject и Owner."""
    coop = Cooperative(name="СТ Ромашка")
    test_db.add(coop)
    await test_db.flush()

    fs = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=coop.id,
        cooperative_id=coop.id,
    )
    owner = Owner(owner_type="physical", name="Иванов И.И.")
    test_db.add_all([fs, owner])
    await test_db.flush()

    payment = Payment(
        financial_subject_id=fs.id,
        payer_owner_id=owner.id,
        amount=Decimal("100.50"),
        payment_date=date(2026, 2, 10),
        document_number="ПП-001",
        description="Членский взнос за январь",
        status="confirmed",
    )
    test_db.add(payment)
    await test_db.commit()
    await test_db.refresh(payment)

    assert payment.id is not None
    assert payment.financial_subject_id == fs.id
    assert payment.payer_owner_id == owner.id
    assert payment.amount == Decimal("100.50")
    assert payment.payment_date == date(2026, 2, 10)
    assert payment.document_number == "ПП-001"
    assert payment.description == "Членский взнос за январь"
    assert payment.status == "confirmed"
    assert payment.created_at is not None
    assert isinstance(payment.created_at, datetime)


@pytest.mark.asyncio
async def test_payment_statuses_confirmed_cancelled(test_db: AsyncSession) -> None:
    """Проверка статусов: confirmed → cancelled."""
    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    fs = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=coop.id,
        cooperative_id=coop.id,
    )
    owner = Owner(owner_type="physical", name="Петров П.П.")
    test_db.add_all([fs, owner])
    await test_db.flush()

    payment = Payment(
        financial_subject_id=fs.id,
        payer_owner_id=owner.id,
        amount=Decimal("50.00"),
        payment_date=date(2026, 2, 1),
        status="confirmed",
    )
    test_db.add(payment)
    await test_db.commit()
    await test_db.refresh(payment)

    assert payment.status == "confirmed"
    payment.status = "cancelled"
    await test_db.commit()
    await test_db.refresh(payment)
    assert payment.status == "cancelled"


@pytest.mark.asyncio
async def test_payment_amount_positive_required(test_db: AsyncSession) -> None:
    """Валидация amount > 0: положительная сумма сохраняется."""
    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    fs = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=coop.id,
        cooperative_id=coop.id,
    )
    owner = Owner(owner_type="physical", name="Сидоров С.С.")
    test_db.add_all([fs, owner])
    await test_db.flush()

    payment = Payment(
        financial_subject_id=fs.id,
        payer_owner_id=owner.id,
        amount=Decimal("0.01"),
        payment_date=date(2026, 2, 1),
        status="confirmed",
    )
    test_db.add(payment)
    await test_db.commit()
    await test_db.refresh(payment)
    assert payment.amount == Decimal("0.01")


@pytest.mark.asyncio
async def test_payment_amount_zero_rejected(test_db: AsyncSession) -> None:
    """Валидация amount > 0: ноль отклоняется БД."""
    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    fs = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=coop.id,
        cooperative_id=coop.id,
    )
    owner = Owner(owner_type="physical", name="Нулев Н.Н.")
    test_db.add_all([fs, owner])
    await test_db.flush()

    payment = Payment(
        financial_subject_id=fs.id,
        payer_owner_id=owner.id,
        amount=Decimal("0.00"),
        payment_date=date(2026, 2, 1),
        status="confirmed",
    )
    test_db.add(payment)
    with pytest.raises(IntegrityError):
        await test_db.commit()
    await test_db.rollback()
