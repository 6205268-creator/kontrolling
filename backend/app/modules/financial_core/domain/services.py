"""Domain services for financial_core module.

Pure Python - no framework dependencies.
"""

from decimal import Decimal

from .entities import Balance


class BalanceCalculator:
    """Domain service for balance calculation.
    
    Contains pure domain logic for calculating balances.
    """

    @staticmethod
    def calculate(
        total_accruals: Decimal,
        total_payments: Decimal,
    ) -> Decimal:
        """Calculate balance from accruals and payments.
        
        Args:
            total_accruals: Sum of all applied accruals.
            total_payments: Sum of all confirmed payments.
            
        Returns:
            Balance amount (positive = debt, negative = credit).
        """
        return total_accruals - total_payments

    @staticmethod
    def is_in_debt(balance: Decimal) -> bool:
        """Check if balance indicates debt."""
        return balance > Decimal("0.00")

    @staticmethod
    def has_credit(balance: Decimal) -> bool:
        """Check if balance indicates overpayment."""
        return balance < Decimal("0.00")
