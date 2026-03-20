"""Integration test: BalanceParticipationRule Python vs SQL consistency.

This test verifies that the Python domain rule (BalanceParticipationRule)
and the SQL translator (BalanceParticipationSqlFilter) produce the same results
when applied to the same data.
"""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.modules.accruals.infrastructure.models import AccrualModel
from app.modules.financial_core.domain.balance_spec import BalanceParticipationRule
from app.modules.financial_core.infrastructure.balance_spec_sql import (
    BalanceParticipationSqlFilter,
)
from app.modules.land_management.infrastructure.models import OwnerModel
from app.modules.payments.infrastructure.models import PaymentModel


@pytest.fixture
async def test_data(test_db):
    """Create test accruals and payments with various dates and statuses."""
    from app.modules.accruals.infrastructure.models import ContributionTypeModel
    from app.modules.cooperative_core.infrastructure.models import CooperativeModel
    from app.modules.financial_core.infrastructure.models import FinancialSubjectModel
    from app.modules.land_management.infrastructure.models import LandPlotModel

    # Create cooperative and financial subject
    coop = CooperativeModel(name="СТ Тест Согласованности", unp="999999999")
    test_db.add(coop)
    await test_db.flush()

    plot = LandPlotModel(cooperative_id=coop.id, plot_number="Тест", area_sqm=Decimal("600.00"))
    test_db.add(plot)
    await test_db.flush()

    subject = FinancialSubjectModel(
        subject_type="LAND_PLOT",
        subject_id=plot.id,
        cooperative_id=coop.id,
        code="FS-CONSISTENCY",
    )
    test_db.add(subject)
    await test_db.flush()

    # Create contribution type
    ct = ContributionTypeModel(name="Тестовый", code="TEST", description="Для тестов")
    test_db.add(ct)
    await test_db.flush()

    # Create owner for payments
    owner = OwnerModel(owner_type="physical", name="Тестовый владелец", tax_id="123456789T")
    test_db.add(owner)
    await test_db.flush()

    # Test dates
    as_of_date = date(2025, 3, 15)

    # Create accruals with different scenarios
    accruals_data = [
        # (accrual_date, created_at, status, cancelled_at, expected_participates)
        (date(2025, 3, 1), datetime(2025, 3, 2, 10, 0, tzinfo=UTC), "applied", None, True),
        (date(2025, 3, 15), datetime(2025, 3, 15, 10, 0, tzinfo=UTC), "applied", None, True),
        (date(2025, 3, 20), datetime(2025, 3, 2, 10, 0, tzinfo=UTC), "applied", None, False),
        (date(2025, 3, 1), datetime(2025, 3, 20, 10, 0, tzinfo=UTC), "applied", None, False),
        (
            date(2025, 3, 1),
            datetime(2025, 3, 2, 10, 0, tzinfo=UTC),
            "cancelled",
            datetime(2025, 3, 20, 10, 0, tzinfo=UTC),
            True,
        ),
        (
            date(2025, 3, 1),
            datetime(2025, 3, 2, 10, 0, tzinfo=UTC),
            "cancelled",
            datetime(2025, 3, 15, 10, 0, tzinfo=UTC),
            False,
        ),
        (
            date(2025, 3, 1),
            datetime(2025, 3, 2, 10, 0, tzinfo=UTC),
            "cancelled",
            datetime(2025, 3, 10, 10, 0, tzinfo=UTC),
            False,
        ),
        (date(2025, 3, 1), datetime(2025, 3, 2, 10, 0, tzinfo=UTC), "created", None, False),
    ]

    accruals = []
    for i, (accrual_date, created_at, status, cancelled_at, expected) in enumerate(accruals_data):
        accrual = AccrualModel(
            id=uuid4(),
            financial_subject_id=subject.id,
            contribution_type_id=ct.id,
            amount=Decimal("100.00"),
            accrual_date=accrual_date,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            status=status,
            created_at=created_at,
            cancelled_at=cancelled_at,
            operation_number=f"ACC-CONSISTENCY-{i}",
        )
        test_db.add(accrual)
        accruals.append((accrual, expected))

    # Create payments with different scenarios
    payments_data = [
        # (payment_date, created_at, status, cancelled_at, expected_participates)
        (date(2025, 3, 1), datetime(2025, 3, 2, 10, 0, tzinfo=UTC), "confirmed", None, True),
        (date(2025, 3, 15), datetime(2025, 3, 15, 10, 0, tzinfo=UTC), "confirmed", None, True),
        (date(2025, 3, 20), datetime(2025, 3, 2, 10, 0, tzinfo=UTC), "confirmed", None, False),
        (date(2025, 3, 1), datetime(2025, 3, 20, 10, 0, tzinfo=UTC), "confirmed", None, False),
        (
            date(2025, 3, 1),
            datetime(2025, 3, 2, 10, 0, tzinfo=UTC),
            "cancelled",
            datetime(2025, 3, 20, 10, 0, tzinfo=UTC),
            True,
        ),
        (
            date(2025, 3, 1),
            datetime(2025, 3, 2, 10, 0, tzinfo=UTC),
            "cancelled",
            datetime(2025, 3, 15, 10, 0, tzinfo=UTC),
            False,
        ),
        (
            date(2025, 3, 1),
            datetime(2025, 3, 2, 10, 0, tzinfo=UTC),
            "cancelled",
            datetime(2025, 3, 10, 10, 0, tzinfo=UTC),
            False,
        ),
        (date(2025, 3, 1), datetime(2025, 3, 2, 10, 0, tzinfo=UTC), "pending", None, False),
    ]

    payments = []
    for i, (payment_date, created_at, status, cancelled_at, expected) in enumerate(payments_data):
        payment = PaymentModel(
            id=uuid4(),
            financial_subject_id=subject.id,
            payer_owner_id=owner.id,
            amount=Decimal("50.00"),
            payment_date=payment_date,
            status=status,
            created_at=created_at,
            cancelled_at=cancelled_at,
            operation_number=f"PAY-CONSISTENCY-{i}",
        )
        test_db.add(payment)
        payments.append((payment, expected))

    await test_db.commit()

    return {
        "as_of_date": as_of_date,
        "accruals": [(a.id, a.accrual_date, a.created_at.date(), a.status, a.cancelled_at.date() if a.cancelled_at else None, expected) 
                     for a, expected in [(acc[0], acc[1]) for acc in accruals]],
        "payments": [(p.id, p.payment_date, p.created_at.date(), p.status, p.cancelled_at.date() if p.cancelled_at else None, expected) 
                     for p, expected in [(pay[0], pay[1]) for pay in payments]],
    }


class TestBalanceParticipationConsistency:
    """Test that Python rule and SQL filter produce same results."""

    @pytest.mark.asyncio
    async def test_accrual_consistency(self, test_db, test_data):
        """Verify Python and SQL accrual filters match for all test cases."""
        rule = BalanceParticipationRule(test_data["as_of_date"])
        sql_filter = BalanceParticipationSqlFilter(rule)

        for accrual_id, accrual_date, created_at_date, status, cancelled_at_date, expected in test_data["accruals"]:
            # Python rule
            python_result = rule.accrual_participates(
                accrual_date=accrual_date,
                created_at_date=created_at_date,
                status=status,
                cancelled_at_date=cancelled_at_date,
            )

            # SQL filter
            sql_result = await test_db.execute(
                select(func.count()).where(
                    sql_filter.accrual_filter(AccrualModel),
                    AccrualModel.id == accrual_id,
                )
            )
            sql_participates = sql_result.scalar() > 0

            assert python_result == sql_participates, (
                f"Mismatch for accrual {accrual_id}: "
                f"Python={python_result}, SQL={sql_participates}, "
                f"dates={accrual_date}/{created_at_date}, status={status}, cancelled={cancelled_at_date}"
            )

    @pytest.mark.asyncio
    async def test_payment_consistency(self, test_db, test_data):
        """Verify Python and SQL payment filters match for all test cases."""
        rule = BalanceParticipationRule(test_data["as_of_date"])
        sql_filter = BalanceParticipationSqlFilter(rule)

        for payment_id, payment_date, created_at_date, status, cancelled_at_date, expected in test_data["payments"]:
            # Python rule
            python_result = rule.payment_participates(
                payment_date=payment_date,
                created_at_date=created_at_date,
                status=status,
                cancelled_at_date=cancelled_at_date,
            )

            # SQL filter
            sql_result = await test_db.execute(
                select(func.count()).where(
                    sql_filter.payment_filter(PaymentModel),
                    PaymentModel.id == payment_id,
                )
            )
            sql_participates = sql_result.scalar() > 0

            assert python_result == sql_participates, (
                f"Mismatch for payment {payment_id}: "
                f"Python={python_result}, SQL={sql_participates}, "
                f"dates={payment_date}/{created_at_date}, status={status}, cancelled={cancelled_at_date}"
            )
