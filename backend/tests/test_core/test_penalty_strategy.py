"""Стратегия и калькулятор пеней (фаза 5)."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.modules.financial_core.application.penalty_use_cases import pick_penalty_settings
from app.modules.financial_core.domain.entities import DebtLine, PenaltySettings
from app.modules.financial_core.domain.penalty_strategy import (
    PenaltyCalculator,
    SimpleDailyPenaltyStrategy,
)
from app.modules.shared.kernel.money import Money


def test_simple_daily_zero_days() -> None:
    s = SimpleDailyPenaltyStrategy()
    ps = PenaltySettings(
        cooperative_id=uuid4(),
        is_enabled=True,
        daily_rate=Decimal("0.01"),
        grace_period_days=0,
        effective_from=date(2020, 1, 1),
    )
    m = s.calculate(Money(Decimal("100.00")), 0, ps)
    assert m.is_zero


def test_simple_daily_positive() -> None:
    s = SimpleDailyPenaltyStrategy()
    ps = PenaltySettings(
        cooperative_id=uuid4(),
        is_enabled=True,
        daily_rate=Decimal("0.01"),
        grace_period_days=0,
        effective_from=date(2020, 1, 1),
    )
    m = s.calculate(Money(Decimal("100.00")), 5, ps)
    assert m.amount == Decimal("5.00")


def test_calculator_disabled_settings() -> None:
    calc = PenaltyCalculator(SimpleDailyPenaltyStrategy())
    dl = DebtLine(
        cooperative_id=uuid4(),
        financial_subject_id=uuid4(),
        accrual_id=uuid4(),
        contribution_type_id=uuid4(),
        original_amount=Money(Decimal("50.00")),
        paid_amount=Money.zero(),
        due_date=date(2026, 1, 1),
        overdue_since=date(2026, 1, 2),
        status="active",
    )
    ps = PenaltySettings(
        cooperative_id=uuid4(),
        is_enabled=False,
        daily_rate=Decimal("0.001"),
        grace_period_days=0,
        effective_from=date(2020, 1, 1),
    )
    assert calc.calculate(dl, ps, date(2026, 2, 1)).is_zero


def test_calculator_before_grace_end() -> None:
    calc = PenaltyCalculator(SimpleDailyPenaltyStrategy())
    dl = DebtLine(
        cooperative_id=uuid4(),
        financial_subject_id=uuid4(),
        accrual_id=uuid4(),
        contribution_type_id=uuid4(),
        original_amount=Money(Decimal("100.00")),
        paid_amount=Money.zero(),
        due_date=date(2026, 1, 10),
        overdue_since=date(2026, 1, 11),
        status="active",
    )
    ps = PenaltySettings(
        cooperative_id=uuid4(),
        is_enabled=True,
        daily_rate=Decimal("1"),
        grace_period_days=10,
        effective_from=date(2020, 1, 1),
    )
    # penalty_start = Jan 21; as_of Jan 20 -> zero
    assert calc.calculate(dl, ps, date(2026, 1, 20)).is_zero


def test_calculator_after_grace() -> None:
    calc = PenaltyCalculator(SimpleDailyPenaltyStrategy())
    dl = DebtLine(
        cooperative_id=uuid4(),
        financial_subject_id=uuid4(),
        accrual_id=uuid4(),
        contribution_type_id=uuid4(),
        original_amount=Money(Decimal("100.00")),
        paid_amount=Money.zero(),
        due_date=date(2026, 1, 10),
        overdue_since=date(2026, 1, 11),
        status="active",
    )
    ps = PenaltySettings(
        cooperative_id=uuid4(),
        is_enabled=True,
        daily_rate=Decimal("0.01"),
        grace_period_days=10,
        effective_from=date(2020, 1, 1),
    )
    # penalty_start Jan 21; as_of Jan 21 -> 1 day * 0.01 * 100 = 1.00
    m = calc.calculate(dl, ps, date(2026, 1, 21))
    assert m.amount == Decimal("1.00")


def test_calculator_partial_payment_reduces_base() -> None:
    calc = PenaltyCalculator(SimpleDailyPenaltyStrategy())
    dl = DebtLine(
        cooperative_id=uuid4(),
        financial_subject_id=uuid4(),
        accrual_id=uuid4(),
        contribution_type_id=uuid4(),
        original_amount=Money(Decimal("100.00")),
        paid_amount=Money(Decimal("60.00")),
        due_date=date(2026, 1, 1),
        overdue_since=date(2026, 1, 2),
        status="active",
    )
    ps = PenaltySettings(
        cooperative_id=uuid4(),
        is_enabled=True,
        daily_rate=Decimal("0.1"),
        grace_period_days=0,
        effective_from=date(2020, 1, 1),
    )
    # outstanding 40, 2 days -> 40 * 0.1 * 2 = 8
    m = calc.calculate(dl, ps, date(2026, 1, 3))
    assert m.amount == Decimal("8.00")


def test_calculator_paid_line() -> None:
    calc = PenaltyCalculator(SimpleDailyPenaltyStrategy())
    dl = DebtLine(
        cooperative_id=uuid4(),
        financial_subject_id=uuid4(),
        accrual_id=uuid4(),
        contribution_type_id=uuid4(),
        original_amount=Money(Decimal("10.00")),
        paid_amount=Money(Decimal("10.00")),
        due_date=date(2026, 1, 1),
        overdue_since=date(2026, 1, 2),
        status="paid",
    )
    ps = PenaltySettings(
        cooperative_id=uuid4(),
        is_enabled=True,
        daily_rate=Decimal("1"),
        grace_period_days=0,
        effective_from=date(2020, 1, 1),
    )
    assert calc.calculate(dl, ps, date(2026, 6, 1)).is_zero


def test_pick_penalty_settings_prefers_specific_type() -> None:
    cid = uuid4()
    tid = uuid4()
    rows = [
        PenaltySettings(
            id=uuid4(),
            cooperative_id=cid,
            contribution_type_id=None,
            is_enabled=True,
            daily_rate=Decimal("0.01"),
            grace_period_days=0,
            effective_from=date(2020, 1, 1),
        ),
        PenaltySettings(
            id=uuid4(),
            cooperative_id=cid,
            contribution_type_id=tid,
            is_enabled=True,
            daily_rate=Decimal("0.05"),
            grace_period_days=0,
            effective_from=date(2021, 1, 1),
        ),
    ]
    picked = pick_penalty_settings(rows, tid, date(2025, 1, 1))
    assert picked is not None
    assert picked.daily_rate == Decimal("0.05")


def test_calculator_no_due_date() -> None:
    calc = PenaltyCalculator(SimpleDailyPenaltyStrategy())
    dl = DebtLine(
        cooperative_id=uuid4(),
        financial_subject_id=uuid4(),
        accrual_id=uuid4(),
        contribution_type_id=uuid4(),
        original_amount=Money(Decimal("10.00")),
        paid_amount=Money.zero(),
        due_date=None,
        overdue_since=None,
        status="active",
    )
    ps = PenaltySettings(
        cooperative_id=uuid4(),
        is_enabled=True,
        daily_rate=Decimal("1"),
        grace_period_days=0,
        effective_from=date(2020, 1, 1),
    )
    assert calc.calculate(dl, ps, date(2026, 6, 1)).is_zero
