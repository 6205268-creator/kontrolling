"""Money Value Object.

Provides type-safe monetary amount handling with BYN currency support.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True)
class Money:
    """Money value object for BYN currency.

    Immutable value object that ensures:
    - Type safety (cannot accidentally add amount to non-amount)
    - Consistent rounding (2 decimal places for BYN)
    - Clear intent in domain models

    Usage:
        m1 = Money(Decimal("10.50"))
        m2 = Money(10.50)  # Also works, converts to Decimal
        total = m1 + m2
        rounded = m1.rounded()
    """

    amount: Decimal

    CURRENCY = "BYN"
    PRECISION = Decimal("0.01")

    def __post_init__(self):
        """Ensure amount is Decimal."""
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))

    def __add__(self, other: "Money") -> "Money":
        """Add two Money amounts."""
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.amount + other.amount)

    def __sub__(self, other: "Money") -> "Money":
        """Subtract two Money amounts."""
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.amount - other.amount)

    def __neg__(self) -> "Money":
        """Negate Money amount."""
        return Money(-self.amount)

    def __gt__(self, other: "Money") -> bool:
        """Greater than comparison."""
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount > other.amount

    def __ge__(self, other: "Money") -> bool:
        """Greater than or equal comparison."""
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount >= other.amount

    def __lt__(self, other: "Money") -> bool:
        """Less than comparison."""
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        """Less than or equal comparison."""
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount <= other.amount

    def __eq__(self, other: object) -> bool:
        """Equality comparison."""
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount

    def __hash__(self) -> int:
        """Hash based on amount."""
        return hash(self.amount)

    def rounded(self) -> "Money":
        """Round to BYN precision (2 decimal places)."""
        return Money(
            self.amount.quantize(self.PRECISION, rounding=ROUND_HALF_UP)
        )

    @property
    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self.amount == Decimal("0")

    @property
    def is_positive(self) -> bool:
        """Check if amount is positive."""
        return self.amount > Decimal("0")

    @property
    def is_negative(self) -> bool:
        """Check if amount is negative."""
        return self.amount < Decimal("0")

    @classmethod
    def zero(cls) -> "Money":
        """Create Money with zero amount."""
        return cls(Decimal("0"))

    def to_decimal(self) -> Decimal:
        """Convert to Decimal for persistence layer."""
        return self.amount

    def __str__(self) -> str:
        """String representation with currency."""
        return f"{self.amount} {self.CURRENCY}"

    def __repr__(self) -> str:
        """Repr for debugging."""
        return f"Money({self.amount!r})"
