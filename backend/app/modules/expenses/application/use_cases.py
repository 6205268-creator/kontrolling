"""Use cases for expenses module."""

from uuid import UUID

from app.modules.shared.kernel.exceptions import ValidationError

from .dtos import ExpenseCreate
from ..domain.entities import Expense
from ..domain.repositories import IExpenseRepository, IExpenseCategoryRepository


class CreateExpenseUseCase:
    """Use case for creating an Expense."""

    def __init__(self, repo: IExpenseRepository):
        self.repo = repo

    async def execute(self, data: ExpenseCreate, cooperative_id: UUID) -> Expense:
        """Create a new expense."""
        if data.amount <= 0:
            raise ValidationError("Amount must be positive")

        entity = Expense(
            id=UUID(int=0),
            cooperative_id=data.cooperative_id,
            category_id=data.category_id,
            amount=data.amount,
            expense_date=data.expense_date,
            document_number=data.document_number,
            description=data.description,
            status="created",
        )
        return await self.repo.add(entity)


class GetExpenseUseCase:
    """Use case for getting an Expense by ID."""

    def __init__(self, repo: IExpenseRepository):
        self.repo = repo

    async def execute(self, expense_id: UUID, cooperative_id: UUID) -> Expense | None:
        """Get expense by ID."""
        return await self.repo.get_by_id(expense_id, cooperative_id)


class GetExpensesByCooperativeUseCase:
    """Use case for getting expenses by cooperative."""

    def __init__(self, repo: IExpenseRepository):
        self.repo = repo

    async def execute(self, cooperative_id: UUID) -> list[Expense]:
        """Get all expenses for a cooperative."""
        return await self.repo.get_by_cooperative(cooperative_id)


class ConfirmExpenseUseCase:
    """Use case for confirming an Expense."""

    def __init__(self, repo: IExpenseRepository):
        self.repo = repo

    async def execute(self, expense_id: UUID, cooperative_id: UUID) -> Expense:
        """Confirm expense (status: created → confirmed)."""
        expense = await self.repo.get_by_id(expense_id, cooperative_id)
        if expense is None:
            raise ValidationError("Expense not found")
        if expense.status != "created":
            raise ValidationError(f"Cannot confirm expense with status '{expense.status}'")
        expense.status = "confirmed"
        return await self.repo.update(expense)


class CancelExpenseUseCase:
    """Use case for cancelling an Expense."""

    def __init__(self, repo: IExpenseRepository):
        self.repo = repo

    async def execute(self, expense_id: UUID, cooperative_id: UUID) -> Expense:
        """Cancel expense (status → cancelled)."""
        expense = await self.repo.get_by_id(expense_id, cooperative_id)
        if expense is None:
            raise ValidationError("Expense not found")
        if expense.status == "cancelled":
            raise ValidationError("Expense is already cancelled")
        expense.status = "cancelled"
        return await self.repo.update(expense)


class GetExpenseCategoriesUseCase:
    """Use case for getting expense categories."""

    def __init__(self, repo: IExpenseCategoryRepository):
        self.repo = repo

    async def execute(self) -> list:
        """Get all expense categories."""
        return await self.repo.get_all(UUID(int=0))
