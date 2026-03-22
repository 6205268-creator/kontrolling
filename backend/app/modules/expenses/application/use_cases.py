"""Use cases for expenses module."""

import uuid
from datetime import datetime
from uuid import UUID

from app.modules.shared.kernel.exceptions import ValidationError

from ..domain.entities import Expense
from ..domain.repositories import IExpenseCategoryRepository, IExpenseRepository
from .dtos import ExpenseCreate


class CreateExpenseUseCase:
    """Use case for creating an Expense."""

    def __init__(self, repo: IExpenseRepository, category_repo: IExpenseCategoryRepository):
        self.repo = repo
        self.category_repo = category_repo

    async def execute(self, data: ExpenseCreate, cooperative_id: UUID | None) -> Expense:
        """Create a new expense."""
        if data.amount <= 0:
            raise ValidationError("Amount must be positive")

        category = await self.category_repo.get_by_id(data.category_id)
        if category is None:
            raise ValidationError("Category not found")

        operation_number = f"EXP-{data.cooperative_id.hex[:8]}-{uuid.uuid4().hex[:8]}"
        entity = Expense(
            id=uuid.uuid4(),
            cooperative_id=data.cooperative_id,
            category_id=data.category_id,
            amount=data.amount,
            expense_date=data.expense_date,
            document_number=data.document_number,
            description=data.description,
            status="created",
            operation_number=operation_number,
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

    async def execute(
        self,
        expense_id: UUID,
        cooperative_id: UUID,
        cancelled_by_user_id: UUID,
        cancellation_reason: str | None = None,
        cancelled_at: datetime | None = None,
    ) -> Expense:
        """Cancel expense (status → cancelled).

        Args:
            expense_id: ID of expense to cancel.
            cooperative_id: ID of cooperative for access control.
            cancelled_by_user_id: ID of user cancelling the expense.
            cancellation_reason: Reason for cancellation (optional).
            cancelled_at: Cancellation datetime (defaults to now).

        Returns:
            Updated Expense entity.

        Raises:
            ValidationError: If expense not found or already cancelled.
        """
        from datetime import UTC

        expense = await self.repo.get_by_id(expense_id, cooperative_id)
        if expense is None:
            raise ValidationError("Expense not found")

        # Use entity method for cancellation (Rich Domain pattern)
        expense.cancel(
            cancelled_by=cancelled_by_user_id,
            reason=cancellation_reason,
            now=cancelled_at or datetime.now(UTC),
        )
        return await self.repo.update(expense)


class GetExpenseCategoriesUseCase:
    """Use case for getting expense categories."""

    def __init__(self, repo: IExpenseCategoryRepository):
        self.repo = repo

    async def execute(self) -> list:
        """Get all expense categories."""
        return await self.repo.get_all()
