"""Tests for Money Value Object."""

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.modules.shared.kernel.money import Money


class TestMoneyCreation:
    """Test Money creation and initialization."""

    def test_create_from_decimal(self):
        """Test creating Money from Decimal."""
        m = Money(Decimal("10.50"))
        assert m.amount == Decimal("10.50")

    def test_create_from_float(self):
        """Test creating Money from float (converts to Decimal)."""
        m = Money(10.50)
        assert m.amount == Decimal("10.50")

    def test_create_from_string(self):
        """Test creating Money from string."""
        m = Money("10.50")
        assert m.amount == Decimal("10.50")

    def test_create_from_int(self):
        """Test creating Money from integer."""
        m = Money(10)
        assert m.amount == Decimal("10")


class TestMoneyArithmetic:
    """Test Money arithmetic operations."""

    def test_add(self):
        """Test adding two Money amounts."""
        m1 = Money(Decimal("10.50"))
        m2 = Money(Decimal("5.25"))
        result = m1 + m2
        assert result.amount == Decimal("15.75")

    def test_sub(self):
        """Test subtracting two Money amounts."""
        m1 = Money(Decimal("10.50"))
        m2 = Money(Decimal("5.25"))
        result = m1 - m2
        assert result.amount == Decimal("5.25")

    def test_neg(self):
        """Test negating Money amount."""
        m = Money(Decimal("10.50"))
        result = -m
        assert result.amount == Decimal("-10.50")

    def test_add_type_safety(self):
        """Test that adding non-Money raises TypeError."""
        m = Money(Decimal("10.50"))
        with pytest.raises(TypeError):
            _ = m + 5  # type: ignore[operator]


class TestMoneyComparison:
    """Test Money comparison operations."""

    def test_greater_than(self):
        """Test greater than comparison."""
        m1 = Money(Decimal("10.50"))
        m2 = Money(Decimal("5.25"))
        assert m1 > m2
        assert not m2 > m1

    def test_greater_equal(self):
        """Test greater than or equal comparison."""
        m1 = Money(Decimal("10.50"))
        m2 = Money(Decimal("10.50"))
        assert m1 >= m2
        assert m2 >= m1

    def test_less_than(self):
        """Test less than comparison."""
        m1 = Money(Decimal("5.25"))
        m2 = Money(Decimal("10.50"))
        assert m1 < m2
        assert not m2 < m1

    def test_less_equal(self):
        """Test less than or equal comparison."""
        m1 = Money(Decimal("10.50"))
        m2 = Money(Decimal("10.50"))
        assert m1 <= m2
        assert m2 <= m1

    def test_equal(self):
        """Test equality comparison."""
        m1 = Money(Decimal("10.50"))
        m2 = Money(Decimal("10.50"))
        assert m1 == m2

    def test_not_equal(self):
        """Test inequality comparison."""
        m1 = Money(Decimal("10.50"))
        m2 = Money(Decimal("5.25"))
        assert m1 != m2


class TestMoneyRounding:
    """Test Money rounding."""

    def test_round_up(self):
        """Test rounding up (ROUND_HALF_UP)."""
        m = Money(Decimal("10.005"))
        rounded = m.rounded()
        assert rounded.amount == Decimal("10.01")

    def test_round_down(self):
        """Test rounding down."""
        m = Money(Decimal("10.004"))
        rounded = m.rounded()
        assert rounded.amount == Decimal("10.00")

    def test_round_half_up(self):
        """Test ROUND_HALF_UP behavior."""
        m = Money(Decimal("10.005"))
        rounded = m.rounded()
        assert rounded.amount == Decimal("10.01")

    def test_round_negative(self):
        """Test rounding negative amounts."""
        m = Money(Decimal("-10.005"))
        rounded = m.rounded()
        assert rounded.amount == Decimal("-10.01")


class TestMoneyProperties:
    """Test Money property checks."""

    def test_is_zero(self):
        """Test is_zero property."""
        assert Money.zero().is_zero
        assert not Money(Decimal("10.50")).is_zero

    def test_is_positive(self):
        """Test is_positive property."""
        assert Money(Decimal("10.50")).is_positive
        assert not Money(Decimal("0")).is_positive
        assert not Money(Decimal("-10.50")).is_positive

    def test_is_negative(self):
        """Test is_negative property."""
        assert Money(Decimal("-10.50")).is_negative
        assert not Money(Decimal("0")).is_negative
        assert not Money(Decimal("10.50")).is_negative

    def test_zero_factory(self):
        """Test Money.zero() factory method."""
        m = Money.zero()
        assert m.amount == Decimal("0")
        assert m.is_zero


class TestMoneyString:
    """Test Money string representation."""

    def test_str(self):
        """Test __str__ method."""
        m = Money(Decimal("10.50"))
        assert str(m) == "10.50 BYN"

    def test_repr(self):
        """Test __repr__ method."""
        m = Money(Decimal("10.50"))
        assert repr(m) == "Money(Decimal('10.50'))"

    def test_to_decimal(self):
        """Test to_decimal method."""
        m = Money(Decimal("10.50"))
        assert m.to_decimal() == Decimal("10.50")


class TestMoneyImmutability:
    """Test Money immutability."""

    def test_frozen(self):
        """Test that Money is frozen (immutable)."""
        m = Money(Decimal("10.50"))
        with pytest.raises(FrozenInstanceError):
            m.amount = Decimal("20.00")  # type: ignore[misc]

    def test_hash(self):
        """Test that Money is hashable."""
        m1 = Money(Decimal("10.50"))
        m2 = Money(Decimal("10.50"))
        assert hash(m1) == hash(m2)

        # Can be used in sets
        money_set = {m1, m2}
        assert len(money_set) == 1
