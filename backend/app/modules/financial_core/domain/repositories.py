"""Financial Core domain repository interfaces.

Pure Python - no framework dependencies (FastAPI, SQLAlchemy, Pydantic).
"""

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.modules.shared.kernel.repositories import IRepository

from .entities import Balance, FinancialSubject


class IFinancialSubjectRepository(IRepository[FinancialSubject], ABC):
    """Repository interface for FinancialSubject operations."""

    @abstractmethod
    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> FinancialSubject | None:
        """Get financial subject by ID, filtered by cooperative."""
        pass

    @abstractmethod
    async def get_all(self, cooperative_id: UUID) -> list[FinancialSubject]:
        """Get all financial subjects for cooperative."""
        pass

    @abstractmethod
    async def get_by_subject(
        self,
        subject_type: str,
        subject_id: UUID,
        cooperative_id: UUID,
    ) -> FinancialSubject | None:
        """Get financial subject by subject type and ID."""
        pass

    @abstractmethod
    async def add(self, entity: FinancialSubject) -> FinancialSubject:
        """Add new financial subject."""
        pass

    @abstractmethod
    async def update(self, entity: FinancialSubject) -> FinancialSubject:
        """Update existing financial subject."""
        pass

    @abstractmethod
    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete financial subject by ID."""
        pass


class IBalanceRepository(ABC):
    """Repository interface for balance calculations.

    Balance is calculated as of a specific date (as_of_date).
    If as_of_date is None, balance is calculated as of today.
    """

    @abstractmethod
    async def calculate_balance(
        self,
        financial_subject_id: UUID,
        as_of_date: date | None = None,
    ) -> Balance | None:
        """Calculate balance for a financial subject as of a specific date.

        Args:
            financial_subject_id: ID of financial subject.
            as_of_date: Date to calculate balance for. If None, uses today's date.

        Returns:
            Balance object or None if subject not found.
        """
        pass

    @abstractmethod
    async def get_balances_by_cooperative(
        self,
        cooperative_id: UUID,
        as_of_date: date | None = None,
    ) -> list[Balance]:
        """Get balances for all financial subjects in cooperative as of a specific date.

        Args:
            cooperative_id: ID of cooperative.
            as_of_date: Date to calculate balances for. If None, uses today's date.

        Returns:
            List of Balance objects.
        """
        pass


class IAccrualAggregateProvider(ABC):
    """Provider for aggregated accrual data.

    This interface allows financial_core to get accrual sums
    without directly importing AccrualModel from accruals module.
    """

    @abstractmethod
    async def sum_participating(
        self,
        financial_subject_id: UUID,
        as_of_date: date,
    ) -> Decimal:
        """Get sum of accruals participating in balance as of date.

        Args:
            financial_subject_id: ID of financial subject.
            as_of_date: Date to calculate sum for.

        Returns:
            Sum of participating accruals.
        """
        pass

    @abstractmethod
    async def sum_participating_by_cooperative(
        self,
        cooperative_id: UUID,
        as_of_date: date,
    ) -> dict[UUID, Decimal]:
        """Get sums of accruals for all subjects in cooperative as of date.

        Args:
            cooperative_id: ID of cooperative.
            as_of_date: Date to calculate sums for.

        Returns:
            Dict mapping financial_subject_id to sum of participating accruals.
        """
        pass


class IPaymentAggregateProvider(ABC):
    """Provider for aggregated payment data.

    This interface allows financial_core to get payment sums
    without directly importing PaymentModel from payments module.
    """

    @abstractmethod
    async def sum_participating(
        self,
        financial_subject_id: UUID,
        as_of_date: date,
    ) -> Decimal:
        """Get sum of payments participating in balance as of date.

        Args:
            financial_subject_id: ID of financial subject.
            as_of_date: Date to calculate sum for.

        Returns:
            Sum of participating payments.
        """
        pass

    @abstractmethod
    async def sum_participating_by_cooperative(
        self,
        cooperative_id: UUID,
        as_of_date: date,
    ) -> dict[UUID, Decimal]:
        """Get sums of payments for all subjects in cooperative as of date.

        Args:
            cooperative_id: ID of cooperative.
            as_of_date: Date to calculate sums for.

        Returns:
            Dict mapping financial_subject_id to sum of participating payments.
        """
        pass
