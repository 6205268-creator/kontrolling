"""Domain services for financial_core module.

Pure Python - no framework dependencies.
"""

from app.modules.shared.kernel.money import Money


class BalanceCalculator:
    """Domain service for balance calculation.

    Contains pure domain logic for calculating balances.
    """

    @staticmethod
    def calculate(total_accruals: Money, total_payments: Money) -> Money:
        """Calculate balance from accruals and payments.

        Args:
            total_accruals: Sum of all applied accruals.
            total_payments: Sum of all confirmed payments.

        Returns:
            Balance amount (positive = debt, negative = credit).
        """
        return Money(total_accruals.amount - total_payments.amount)

    @staticmethod
    def is_in_debt(balance: Money) -> bool:
        """Check if balance indicates debt."""
        return balance.is_positive

    @staticmethod
    def has_credit(balance: Money) -> bool:
        """Check if balance indicates overpayment."""
        return balance.is_negative
