"""Tests for domain events dispatching.

Tests verify that domain events are dispatched when financial operations occur.
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.accruals.domain.events import AccrualApplied, AccrualCancelled
from app.modules.accruals.infrastructure.repositories import AccrualRepository
from app.modules.cooperative_core.infrastructure.models import CooperativeModel as Cooperative
from app.modules.financial_core.infrastructure.models import (
    FinancialSubjectModel as FinancialSubject,
)
from app.modules.payments.domain.events import PaymentCancelled, PaymentConfirmed
from app.modules.payments.infrastructure.repositories import PaymentRepository
from app.modules.shared.kernel.events import EventDispatcher


@pytest.fixture
def event_dispatcher() -> EventDispatcher:
    """Create fresh event dispatcher for each test."""
    dispatcher = EventDispatcher()
    return dispatcher


@pytest.fixture
def captured_events(event_dispatcher: EventDispatcher) -> list:
    """Capture all dispatched events for verification."""
    events = []

    def capture_handler(event):
        events.append(event)

    # Register capture handlers for all financial events
    event_dispatcher.register(PaymentConfirmed, capture_handler)
    event_dispatcher.register(PaymentCancelled, capture_handler)
    event_dispatcher.register(AccrualApplied, capture_handler)
    event_dispatcher.register(AccrualCancelled, capture_handler)

    return events


@pytest.mark.asyncio
async def test_payment_confirmed_event_dispatched(
    test_db: AsyncSession,
    event_dispatcher: EventDispatcher,
    captured_events: list,
) -> None:
    """Test that PaymentConfirmed event is dispatched when payment is registered."""
    from app.modules.land_management.infrastructure.models import OwnerModel as Owner
    from app.modules.payments.application.use_cases import RegisterPaymentUseCase

    # Setup test data
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

    # Create use case with event dispatcher
    repo = PaymentRepository(test_db)
    use_case = RegisterPaymentUseCase(repo, event_dispatcher)

    # Create payment DTO
    from app.modules.payments.application.dtos import PaymentCreate

    payment_data = PaymentCreate(
        financial_subject_id=fs.id,
        payer_owner_id=owner.id,
        amount=Decimal("100.00"),
        payment_date=date(2026, 2, 1),
        document_number="ПП-001",
        description="Тестовый платёж",
    )

    # Execute use case
    result = await use_case.execute(payment_data, coop.id)

    # Verify event was dispatched
    assert len(captured_events) == 1
    assert isinstance(captured_events[0], PaymentConfirmed)
    assert captured_events[0].payment_id == result.id
    assert captured_events[0].amount == Decimal("100.00")


@pytest.mark.asyncio
async def test_payment_cancelled_event_dispatched(
    test_db: AsyncSession,
    event_dispatcher: EventDispatcher,
    captured_events: list,
) -> None:
    """Test that PaymentCancelled event is dispatched when payment is cancelled."""
    from uuid import UUID

    from app.modules.land_management.infrastructure.models import OwnerModel as Owner
    from app.modules.payments.application.use_cases import (
        CancelPaymentUseCase,
    )
    from app.modules.payments.infrastructure.models import PaymentModel as Payment

    # Setup: create payment
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

    payment_model = Payment(
        financial_subject_id=fs.id,
        payer_owner_id=owner.id,
        amount=Decimal("100.00"),
        payment_date=date(2026, 2, 1),
        status="confirmed",
        operation_number="PAY-TEST-001",
    )
    test_db.add(payment_model)
    await test_db.commit()
    await test_db.refresh(payment_model)

    # Cancel payment with event dispatcher
    repo = PaymentRepository(test_db)
    use_case = CancelPaymentUseCase(repo, event_dispatcher)

    user_id = UUID(int=123)
    result = await use_case.execute(
        payment_id=payment_model.id,
        cooperative_id=coop.id,
        cancelled_by_user_id=user_id,
        cancellation_reason="Тестовая отмена",
    )

    # Verify event was dispatched
    assert len(captured_events) == 1
    assert isinstance(captured_events[0], PaymentCancelled)
    assert captured_events[0].payment_id == result.id
    assert captured_events[0].cancelled_by == user_id
    assert captured_events[0].reason == "Тестовая отмена"


@pytest.mark.asyncio
async def test_accrual_applied_event_dispatched(
    test_db: AsyncSession,
    event_dispatcher: EventDispatcher,
    captured_events: list,
) -> None:
    """Test that AccrualApplied event is dispatched when accrual is applied."""
    from app.modules.accruals.application.use_cases import ApplyAccrualUseCase
    from app.modules.accruals.infrastructure.models import (
        AccrualModel as Accrual,
    )
    from app.modules.accruals.infrastructure.models import (
        ContributionTypeModel as ContributionType,
    )

    # Setup: create accrual
    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    fs = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=coop.id,
        cooperative_id=coop.id,
    )
    ct = ContributionType(name="Членский взнос", code="membership")
    test_db.add_all([fs, ct])
    await test_db.flush()

    accrual_model = Accrual(
        financial_subject_id=fs.id,
        contribution_type_id=ct.id,
        amount=Decimal("50.00"),
        accrual_date=date(2026, 1, 15),
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        status="created",
        operation_number="ACC-TEST-001",
    )
    test_db.add(accrual_model)
    await test_db.commit()
    await test_db.refresh(accrual_model)

    # Apply accrual with event dispatcher
    repo = AccrualRepository(test_db)
    use_case = ApplyAccrualUseCase(repo, event_dispatcher)

    result = await use_case.execute(accrual_id=accrual_model.id, cooperative_id=coop.id)

    # Verify event was dispatched
    assert len(captured_events) == 1
    assert isinstance(captured_events[0], AccrualApplied)
    assert captured_events[0].accrual_id == result.id
    assert captured_events[0].amount == Decimal("50.00")


@pytest.mark.asyncio
async def test_accrual_cancelled_event_dispatched(
    test_db: AsyncSession,
    event_dispatcher: EventDispatcher,
    captured_events: list,
) -> None:
    """Test that AccrualCancelled event is dispatched when accrual is cancelled."""
    from uuid import UUID

    from app.modules.accruals.application.use_cases import CancelAccrualUseCase
    from app.modules.accruals.infrastructure.models import (
        AccrualModel as Accrual,
    )
    from app.modules.accruals.infrastructure.models import (
        ContributionTypeModel as ContributionType,
    )

    # Setup: create accrual
    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    fs = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=coop.id,
        cooperative_id=coop.id,
    )
    ct = ContributionType(name="Членский взнос", code="membership")
    test_db.add_all([fs, ct])
    await test_db.flush()

    accrual_model = Accrual(
        financial_subject_id=fs.id,
        contribution_type_id=ct.id,
        amount=Decimal("50.00"),
        accrual_date=date(2026, 1, 15),
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        status="applied",
        operation_number="ACC-TEST-001",
    )
    test_db.add(accrual_model)
    await test_db.commit()
    await test_db.refresh(accrual_model)

    # Cancel accrual with event dispatcher
    repo = AccrualRepository(test_db)
    use_case = CancelAccrualUseCase(repo, event_dispatcher)

    user_id = UUID(int=456)
    result = await use_case.execute(
        accrual_id=accrual_model.id,
        cooperative_id=coop.id,
        cancelled_by_user_id=user_id,
        cancellation_reason="Тестовая отмена начисления",
    )

    # Verify event was dispatched
    assert len(captured_events) == 1
    assert isinstance(captured_events[0], AccrualCancelled)
    assert captured_events[0].accrual_id == result.id
    assert captured_events[0].cancelled_by == user_id
    assert captured_events[0].reason == "Тестовая отмена начисления"
