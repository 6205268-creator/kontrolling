"""Tests for BalanceParticipationRule domain specification."""

from datetime import date

import pytest

from app.modules.financial_core.domain.balance_spec import BalanceParticipationRule


class TestAccrualParticipation:
    """Test accrual_participates method with various scenarios."""

    @pytest.fixture
    def rule(self):
        """Create rule for 2025-03-15."""
        return BalanceParticipationRule(date(2025, 3, 15))

    # Applied accruals

    def test_applied_before_as_of_date(self, rule):
        """Applied accrual with all dates before as_of_date participates."""
        assert rule.accrual_participates(
            accrual_date=date(2025, 3, 1),
            created_at_date=date(2025, 3, 2),
            status="applied",
        ) is True

    def test_applied_on_as_of_date(self, rule):
        """Applied accrual with event_date == as_of_date participates."""
        assert rule.accrual_participates(
            accrual_date=date(2025, 3, 15),
            created_at_date=date(2025, 3, 15),
            status="applied",
        ) is True

    def test_applied_accrual_date_after_as_of_date(self, rule):
        """Applied accrual with accrual_date > as_of_date does NOT participate."""
        assert rule.accrual_participates(
            accrual_date=date(2025, 3, 20),
            created_at_date=date(2025, 3, 2),
            status="applied",
        ) is False

    def test_applied_created_at_after_as_of_date(self, rule):
        """Applied accrual with created_at > as_of_date does NOT participate."""
        assert rule.accrual_participates(
            accrual_date=date(2025, 3, 1),
            created_at_date=date(2025, 3, 20),
            status="applied",
        ) is False

    # Cancelled accruals

    def test_cancelled_after_as_of_date(self, rule):
        """Cancelled accrual with cancelled_at > as_of_date participates."""
        assert rule.accrual_participates(
            accrual_date=date(2025, 3, 1),
            created_at_date=date(2025, 3, 2),
            status="cancelled",
            cancelled_at_date=date(2025, 3, 20),
        ) is True

    def test_cancelled_on_as_of_date(self, rule):
        """Cancelled accrual with cancelled_at == as_of_date does NOT participate."""
        assert rule.accrual_participates(
            accrual_date=date(2025, 3, 1),
            created_at_date=date(2025, 3, 2),
            status="cancelled",
            cancelled_at_date=date(2025, 3, 15),
        ) is False

    def test_cancelled_before_as_of_date(self, rule):
        """Cancelled accrual with cancelled_at < as_of_date does NOT participate."""
        assert rule.accrual_participates(
            accrual_date=date(2025, 3, 1),
            created_at_date=date(2025, 3, 2),
            status="cancelled",
            cancelled_at_date=date(2025, 3, 10),
        ) is False

    def test_cancelled_no_cancelled_at(self, rule):
        """Cancelled accrual with cancelled_at=None does NOT participate."""
        assert rule.accrual_participates(
            accrual_date=date(2025, 3, 1),
            created_at_date=date(2025, 3, 2),
            status="cancelled",
            cancelled_at_date=None,
        ) is False

    # Edge cases

    def test_created_status(self, rule):
        """Accrual with status 'created' does NOT participate."""
        assert rule.accrual_participates(
            accrual_date=date(2025, 3, 1),
            created_at_date=date(2025, 3, 2),
            status="created",
        ) is False

    def test_all_dates_equal_as_of_date(self, rule):
        """All dates equal to as_of_date with applied status participates."""
        assert rule.accrual_participates(
            accrual_date=date(2025, 3, 15),
            created_at_date=date(2025, 3, 15),
            status="applied",
        ) is True


class TestPaymentParticipation:
    """Test payment_participates method with various scenarios."""

    @pytest.fixture
    def rule(self):
        """Create rule for 2025-03-15."""
        return BalanceParticipationRule(date(2025, 3, 15))

    # Confirmed payments

    def test_confirmed_before_as_of_date(self, rule):
        """Confirmed payment with all dates before as_of_date participates."""
        assert rule.payment_participates(
            payment_date=date(2025, 3, 1),
            created_at_date=date(2025, 3, 2),
            status="confirmed",
        ) is True

    def test_confirmed_on_as_of_date(self, rule):
        """Confirmed payment with event_date == as_of_date participates."""
        assert rule.payment_participates(
            payment_date=date(2025, 3, 15),
            created_at_date=date(2025, 3, 15),
            status="confirmed",
        ) is True

    def test_confirmed_payment_date_after_as_of_date(self, rule):
        """Confirmed payment with payment_date > as_of_date does NOT participate."""
        assert rule.payment_participates(
            payment_date=date(2025, 3, 20),
            created_at_date=date(2025, 3, 2),
            status="confirmed",
        ) is False

    def test_confirmed_created_at_after_as_of_date(self, rule):
        """Confirmed payment with created_at > as_of_date does NOT participate."""
        assert rule.payment_participates(
            payment_date=date(2025, 3, 1),
            created_at_date=date(2025, 3, 20),
            status="confirmed",
        ) is False

    # Cancelled payments

    def test_cancelled_after_as_of_date(self, rule):
        """Cancelled payment with cancelled_at > as_of_date participates."""
        assert rule.payment_participates(
            payment_date=date(2025, 3, 1),
            created_at_date=date(2025, 3, 2),
            status="cancelled",
            cancelled_at_date=date(2025, 3, 20),
        ) is True

    def test_cancelled_on_as_of_date(self, rule):
        """Cancelled payment with cancelled_at == as_of_date does NOT participate."""
        assert rule.payment_participates(
            payment_date=date(2025, 3, 1),
            created_at_date=date(2025, 3, 2),
            status="cancelled",
            cancelled_at_date=date(2025, 3, 15),
        ) is False

    def test_cancelled_before_as_of_date(self, rule):
        """Cancelled payment with cancelled_at < as_of_date does NOT participate."""
        assert rule.payment_participates(
            payment_date=date(2025, 3, 1),
            created_at_date=date(2025, 3, 2),
            status="cancelled",
            cancelled_at_date=date(2025, 3, 10),
        ) is False

    def test_cancelled_no_cancelled_at(self, rule):
        """Cancelled payment with cancelled_at=None does NOT participate."""
        assert rule.payment_participates(
            payment_date=date(2025, 3, 1),
            created_at_date=date(2025, 3, 2),
            status="cancelled",
            cancelled_at_date=None,
        ) is False

    # Edge cases

    def test_pending_status(self, rule):
        """Payment with status 'pending' does NOT participate."""
        assert rule.payment_participates(
            payment_date=date(2025, 3, 1),
            created_at_date=date(2025, 3, 2),
            status="pending",
        ) is False

    def test_all_dates_equal_as_of_date(self, rule):
        """All dates equal to as_of_date with confirmed status participates."""
        assert rule.payment_participates(
            payment_date=date(2025, 3, 15),
            created_at_date=date(2025, 3, 15),
            status="confirmed",
        ) is True


class TestBalanceParticipationRuleImmutability:
    """Test that BalanceParticipationRule is immutable."""

    def test_frozen(self):
        """Test that rule is frozen (immutable)."""
        from dataclasses import FrozenInstanceError

        rule = BalanceParticipationRule(date(2025, 3, 15))
        with pytest.raises(FrozenInstanceError):
            rule.as_of_date = date(2025, 3, 16)  # type: ignore[misc]
