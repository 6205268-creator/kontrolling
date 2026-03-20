"""Balance Participation SQL Filter — translator from domain rule to SQLAlchemy.

This module translates BalanceParticipationRule (domain) into SQLAlchemy
WHERE clauses for use in repository queries.
"""

from sqlalchemy import and_, or_
from sqlalchemy.sql.elements import BooleanClauseList

from app.modules.financial_core.domain.balance_spec import BalanceParticipationRule


class BalanceParticipationSqlFilter:
    """Транслирует BalanceParticipationRule в SQLAlchemy WHERE-клаузы.

    Usage:
        rule = BalanceParticipationRule(date(2025, 3, 15))
        sql_filter = BalanceParticipationSqlFilter(rule)

        # For accruals
        accrual_filter = sql_filter.accrual_filter(AccrualModel)
        query = select(func.sum(AccrualModel.amount)).where(accrual_filter)

        # For payments
        payment_filter = sql_filter.payment_filter(PaymentModel)
        query = select(func.sum(PaymentModel.amount)).where(payment_filter)
    """

    def __init__(self, rule: BalanceParticipationRule):
        """Initialize with domain rule.

        Args:
            rule: BalanceParticipationRule instance with as_of_date.
        """
        self._rule = rule

    def accrual_filter(
        self,
        model_class: type,
        financial_subject_id_filter=None,
    ) -> BooleanClauseList:
        """Build SQLAlchemy WHERE clause for accruals.

        Args:
            model_class: AccrualModel class (or any class with same fields).
            financial_subject_id_filter: Optional UUID to filter by financial subject.

        Returns:
            SQLAlchemy BooleanClauseList for use in .where() clause.
        """
        from sqlalchemy import func

        conditions = [
            # Rule 1: accrual_date <= as_of_date
            model_class.accrual_date <= self._rule.as_of_date,

            # Rule 2: date(created_at) <= as_of_date
            func.date(model_class.created_at) <= self._rule.as_of_date,

            # Rule 3: status == 'applied'
            model_class.status == "applied",
        ]

        # OR: status == 'cancelled' AND cancelled_at > as_of_date
        cancelled_condition = and_(
            model_class.status == "cancelled",
            model_class.cancelled_at.isnot(None),
            func.date(model_class.cancelled_at) > self._rule.as_of_date,
        )

        # Combine: applied OR (cancelled after as_of_date)
        status_condition = or_(conditions[2], cancelled_condition)

        # Final filter: date conditions AND status condition
        final_conditions = [conditions[0], conditions[1], status_condition]

        if financial_subject_id_filter is not None:
            final_conditions.append(
                model_class.financial_subject_id == financial_subject_id_filter
            )

        return and_(*final_conditions)

    def payment_filter(
        self,
        model_class: type,
        financial_subject_id_filter=None,
    ) -> BooleanClauseList:
        """Build SQLAlchemy WHERE clause for payments.

        Args:
            model_class: PaymentModel class (or any class with same fields).
            financial_subject_id_filter: Optional UUID to filter by financial subject.

        Returns:
            SQLAlchemy BooleanClauseList for use in .where() clause.
        """
        from sqlalchemy import func

        conditions = [
            # Rule 1: payment_date <= as_of_date
            model_class.payment_date <= self._rule.as_of_date,

            # Rule 2: date(created_at) <= as_of_date
            func.date(model_class.created_at) <= self._rule.as_of_date,

            # Rule 3: status == 'confirmed'
            model_class.status == "confirmed",
        ]

        # OR: status == 'cancelled' AND cancelled_at > as_of_date
        cancelled_condition = and_(
            model_class.status == "cancelled",
            model_class.cancelled_at.isnot(None),
            func.date(model_class.cancelled_at) > self._rule.as_of_date,
        )

        # Combine: confirmed OR (cancelled after as_of_date)
        status_condition = or_(conditions[2], cancelled_condition)

        # Final filter: date conditions AND status condition
        final_conditions = [conditions[0], conditions[1], status_condition]

        if financial_subject_id_filter is not None:
            final_conditions.append(
                model_class.financial_subject_id == financial_subject_id_filter
            )

        return and_(*final_conditions)
