from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cooperative_core.infrastructure.models import CooperativeModel as Cooperative
from app.modules.financial_core.infrastructure.models import (
    FinancialSubjectModel as FinancialSubject,
)
from app.modules.land_management.infrastructure.models import OwnerModel as Owner
from app.modules.payments.infrastructure.models import PaymentModel as Payment


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
        operation_number="PAY-M-1",
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
        operation_number="PAY-M-2",
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
        operation_number="PAY-M-3",
    )
    test_db.add(payment)
    await test_db.flush()


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
        operation_number="PAY-M-4",
    )
    test_db.add(payment)
    with pytest.raises(IntegrityError):
        await test_db.commit()
    await test_db.rollback()


@pytest.mark.asyncio
async def test_payment_amount_immutable_on_update(test_db: AsyncSession) -> None:
    """Этап 4: amount не изменяется при update (immutability)."""
    from app.modules.payments.domain.entities import Payment as PaymentEntity
    from app.modules.payments.infrastructure.repositories import PaymentRepository

    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    fs = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=coop.id,
        cooperative_id=coop.id,
    )
    owner = Owner(owner_type="physical", name="Тестов Т.Т.")
    test_db.add_all([fs, owner])
    await test_db.flush()

    original_amount = Decimal("100.00")
    payment_model = Payment(
        financial_subject_id=fs.id,
        payer_owner_id=owner.id,
        amount=original_amount,
        payment_date=date(2026, 2, 1),
        status="confirmed",
        operation_number="PAY-M-5",
    )
    test_db.add(payment_model)
    await test_db.commit()
    await test_db.refresh(payment_model)

    # Создаём domain entity с изменённым amount (не из сессии)
    entity = PaymentEntity(
        id=payment_model.id,
        financial_subject_id=payment_model.financial_subject_id,
        payer_owner_id=payment_model.payer_owner_id,
        amount=Decimal("999.99"),  # Пытаемся изменить amount
        payment_date=payment_model.payment_date,
        document_number=payment_model.document_number,
        description=payment_model.description,
        status=payment_model.status,
        operation_number=payment_model.operation_number,
    )

    repo = PaymentRepository(test_db)
    updated = await repo.update(entity)

    # amount должен остаться оригинальным (не обновляться в БД)
    assert updated.amount == original_amount, "Amount should be immutable - not updated in repository"
