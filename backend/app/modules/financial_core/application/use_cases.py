"""Use cases for financial_core module."""

from datetime import date
from uuid import UUID

from ..domain.entities import FinancialSubject
from ..domain.events import LandPlotCreated, MeterCreated
from ..domain.repositories import IFinancialSubjectRepository
from .dtos import FinancialSubjectCreate


class CreateFinancialSubjectUseCase:
    """Use case for creating a FinancialSubject.
    
    Typically called by event handler when LandPlot or Meter is created.
    """

    def __init__(self, repo: IFinancialSubjectRepository):
        self.repo = repo

    async def execute(self, data: FinancialSubjectCreate) -> FinancialSubject:
        """Create a new financial subject."""
        entity = FinancialSubject(
            id=UUID(int=0),  # Will be set by repository
            subject_type=data.subject_type,
            subject_id=data.subject_id,
            cooperative_id=data.cooperative_id,
            code=data.code,
            status=data.status,
        )
        
        return await self.repo.add(entity)


class GetFinancialSubjectUseCase:
    """Use case for getting a FinancialSubject by ID."""

    def __init__(self, repo: IFinancialSubjectRepository):
        self.repo = repo

    async def execute(self, subject_id: UUID, cooperative_id: UUID) -> FinancialSubject | None:
        """Get financial subject by ID."""
        return await self.repo.get_by_id(subject_id, cooperative_id)


class GetFinancialSubjectsUseCase:
    """Use case for getting list of FinancialSubjects."""

    def __init__(self, repo: IFinancialSubjectRepository):
        self.repo = repo

    async def execute(self, cooperative_id: UUID) -> list[FinancialSubject]:
        """Get all financial subjects for cooperative."""
        return await self.repo.get_all(cooperative_id)


class GetBalanceUseCase:
    """Use case for getting balance of a FinancialSubject as of a specific date."""

    def __init__(self, balance_repo):
        self.balance_repo = balance_repo

    async def execute(
        self,
        financial_subject_id: UUID,
        as_of_date: date | None = None,
    ) -> dict | None:
        """Get balance for financial subject as of a specific date.
        
        Args:
            financial_subject_id: ID of financial subject.
            as_of_date: Date to calculate balance for. If None, uses today's date.
        """
        return await self.balance_repo.calculate_balance(financial_subject_id, as_of_date)


class GetBalancesByCooperativeUseCase:
    """Use case for getting balances of all FinancialSubjects in cooperative as of a specific date."""

    def __init__(self, balance_repo):
        self.balance_repo = balance_repo

    async def execute(
        self,
        cooperative_id: UUID,
        as_of_date: date | None = None,
    ) -> list[dict]:
        """Get balances for all financial subjects in cooperative as of a specific date.
        
        Args:
            cooperative_id: ID of cooperative.
            as_of_date: Date to calculate balances for. If None, uses today's date.
        """
        return await self.balance_repo.get_balances_by_cooperative(cooperative_id, as_of_date)


# Event Handlers

class LandPlotCreatedHandler:
    """Handler for LandPlotCreated event.
    
    Creates FinancialSubject automatically when a new LandPlot is created.
    """

    def __init__(self, fs_repo: IFinancialSubjectRepository):
        self.fs_repo = fs_repo

    def __call__(self, event: LandPlotCreated) -> None:
        """Handle LandPlotCreated event.
        
        Note: This is a synchronous handler. For async operations,
        use async event bus or background tasks.
        """
        # Note: Actual FS creation should happen in async use case
        # This is a simplified version - in production, use async event handling
        pass  # Will be implemented with async event bus


class MeterCreatedHandler:
    """Handler for MeterCreated event.
    
    Creates FinancialSubject automatically when a new Meter is created.
    """

    def __init__(self, fs_repo: IFinancialSubjectRepository):
        self.fs_repo = fs_repo

    def __call__(self, event: MeterCreated) -> None:
        """Handle MeterCreated event."""
        pass  # Will be implemented with async event bus
