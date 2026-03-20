"""Balance Participation Rule — domain specification.

Pure Python — no framework dependencies.

This module defines the rule for which operations participate in balance
calculation as of a specific date, according to ADR 0002.
"""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class BalanceParticipationRule:
    """Правило: участвует ли операция в балансе на дату as_of_date.

    According to ADR 0002, operation participates in balance on date X if:
    1. event_date <= X (accrual_date for Accrual, payment_date for Payment)
    2. date(created_at) <= X
    3. status is correct:
       - For Accrual: status == 'applied' OR (status == 'cancelled' AND cancelled_at > X)
       - For Payment: status == 'confirmed' OR (status == 'cancelled' AND cancelled_at > X)

    Usage:
        rule = BalanceParticipationRule(date(2025, 3, 15))
        participates = rule.accrual_participates(
            accrual_date=date(2025, 3, 1),
            created_at_date=date(2025, 3, 2),
            status="applied",
            cancelled_at_date=None
        )
    """

    as_of_date: date

    def accrual_participates(
        self,
        accrual_date: date,
        created_at_date: date,
        status: str,
        cancelled_at_date: date | None = None,
    ) -> bool:
        """Check if accrual participates in balance as of as_of_date.

        Args:
            accrual_date: Date when accrual was made (event_date).
            created_at_date: Date when accrual record was created.
            status: Accrual status (applied, cancelled, etc.).
            cancelled_at_date: Date when accrual was cancelled (if applicable).

        Returns:
            True if accrual participates in balance calculation.
        """
        # Rule 1: event_date <= as_of_date
        if accrual_date > self.as_of_date:
            return False

        # Rule 2: created_at_date <= as_of_date
        if created_at_date > self.as_of_date:
            return False

        # Rule 3: status check
        if status == "applied":
            return True

        # Cancelled accrual participates if cancelled AFTER as_of_date
        if status == "cancelled" and cancelled_at_date and cancelled_at_date > self.as_of_date:
            return True

        return False

    def payment_participates(
        self,
        payment_date: date,
        created_at_date: date,
        status: str,
        cancelled_at_date: date | None = None,
    ) -> bool:
        """Check if payment participates in balance as of as_of_date.

        Args:
            payment_date: Date when payment was made (event_date).
            created_at_date: Date when payment record was created.
            status: Payment status (confirmed, cancelled, etc.).
            cancelled_at_date: Date when payment was cancelled (if applicable).

        Returns:
            True if payment participates in balance calculation.
        """
        # Rule 1: event_date <= as_of_date
        if payment_date > self.as_of_date:
            return False

        # Rule 2: created_at_date <= as_of_date
        if created_at_date > self.as_of_date:
            return False

        # Rule 3: status check
        if status == "confirmed":
            return True

        # Cancelled payment participates if cancelled AFTER as_of_date
        if status == "cancelled" and cancelled_at_date and cancelled_at_date > self.as_of_date:
            return True

        return False
