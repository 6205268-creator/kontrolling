"""Financial Core domain repository interfaces.

Pure Python - no framework dependencies (FastAPI, SQLAlchemy, Pydantic).
"""

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.modules.shared.kernel.repositories import IRepository

from .entities import (
    Balance,
    BalanceSnapshot,
    DebtLine,
    FinancialPeriod,
    FinancialSubject,
    PenaltySettings,
)


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

    @abstractmethod
    async def sum_applied_in_period(
        self,
        financial_subject_id: UUID,
        period_start: date,
        period_end: date,
    ) -> Decimal:
        """Сумма начислений со статусом applied за интервал дат (по accrual_date)."""
        pass

    @abstractmethod
    async def sum_applied_in_period_by_cooperative(
        self,
        cooperative_id: UUID,
        period_start: date,
        period_end: date,
    ) -> dict[UUID, Decimal]:
        """Суммы начислений по субъектам СТ за интервал (applied, accrual_date)."""
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

    @abstractmethod
    async def sum_confirmed_in_period(
        self,
        financial_subject_id: UUID,
        period_start: date,
        period_end: date,
    ) -> Decimal:
        """Сумма платежей со статусом confirmed за интервал (по payment_date)."""
        pass

    @abstractmethod
    async def sum_confirmed_in_period_by_cooperative(
        self,
        cooperative_id: UUID,
        period_start: date,
        period_end: date,
    ) -> dict[UUID, Decimal]:
        """Суммы платежей по субъектам СТ за интервал (confirmed, payment_date)."""
        pass


class IFinancialPeriodRepository(IRepository[FinancialPeriod], ABC):
    """Repository interface for FinancialPeriod operations."""

    @abstractmethod
    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> FinancialPeriod | None:
        """Get period by ID, filtered by cooperative."""
        pass

    @abstractmethod
    async def get_by_date(
        self,
        cooperative_id: UUID,
        date: date,
    ) -> FinancialPeriod | None:
        """Get period that contains the given date."""
        pass

    @abstractmethod
    async def get_all(
        self,
        cooperative_id: UUID,
        year: int | None = None,
    ) -> list[FinancialPeriod]:
        """Get all periods for cooperative, optionally filtered by year."""
        pass

    @abstractmethod
    async def get_previous_period(
        self,
        period: FinancialPeriod,
    ) -> FinancialPeriod | None:
        """Get previous period for the same cooperative.

        For monthly: returns previous month or previous year's December.
        For yearly: returns previous year.
        """
        pass

    @abstractmethod
    async def add(self, entity: FinancialPeriod) -> FinancialPeriod:
        """Add new period."""
        pass

    @abstractmethod
    async def update(self, entity: FinancialPeriod) -> FinancialPeriod:
        """Update existing period."""
        pass

    @abstractmethod
    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete period by ID."""
        pass


class IBalanceSnapshotRepository(ABC):
    """Repository interface for BalanceSnapshot operations.

    BalanceSnapshot is a read model for fast balance queries.
    """

    @abstractmethod
    async def get_by_financial_subject(
        self,
        financial_subject_id: UUID,
        period_id: UUID,
    ) -> BalanceSnapshot | None:
        """Get snapshot for financial subject and period."""
        pass

    @abstractmethod
    async def get_by_cooperative(
        self,
        cooperative_id: UUID,
        period_id: UUID,
    ) -> list[BalanceSnapshot]:
        """Get all snapshots for cooperative and period."""
        pass

    @abstractmethod
    async def add(self, entity: BalanceSnapshot) -> BalanceSnapshot:
        """Add new snapshot."""
        pass

    @abstractmethod
    async def delete_by_period(
        self,
        period_id: UUID,
        cooperative_id: UUID,
    ) -> int:
        """Delete all snapshots for period. Returns count of deleted."""
        pass


class IDebtLineRepository(ABC):
    """Репозиторий строк долга (фаза 5)."""

    @abstractmethod
    async def get_by_id(self, line_id: UUID, cooperative_id: UUID) -> DebtLine | None:
        pass

    @abstractmethod
    async def get_by_accrual_id(self, accrual_id: UUID) -> DebtLine | None:
        pass

    @abstractmethod
    async def get_by_financial_subject(
        self,
        financial_subject_id: UUID,
        cooperative_id: UUID,
    ) -> list[DebtLine]:
        pass

    @abstractmethod
    async def get_active_with_outstanding(
        self,
        cooperative_id: UUID,
    ) -> list[DebtLine]:
        """Статус active и остаток > 0."""
        pass

    @abstractmethod
    async def get_overdue(
        self,
        cooperative_id: UUID,
        as_of_date: date,
    ) -> list[DebtLine]:
        """Active, outstanding > 0, overdue_since не позже as_of_date."""
        pass

    @abstractmethod
    async def add(self, entity: DebtLine) -> DebtLine:
        pass

    @abstractmethod
    async def update(self, entity: DebtLine) -> DebtLine:
        pass


class IPenaltySettingsRepository(ABC):
    """Настройки пеней по СТ."""

    @abstractmethod
    async def list_for_cooperative(self, cooperative_id: UUID) -> list[PenaltySettings]:
        pass

    @abstractmethod
    async def get_by_id(self, settings_id: UUID, cooperative_id: UUID) -> PenaltySettings | None:
        pass

    @abstractmethod
    async def add(self, entity: PenaltySettings) -> PenaltySettings:
        pass

    @abstractmethod
    async def update(self, entity: PenaltySettings) -> PenaltySettings:
        pass

    @abstractmethod
    async def delete(self, settings_id: UUID, cooperative_id: UUID) -> None:
        pass
