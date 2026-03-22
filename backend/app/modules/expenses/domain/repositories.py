"""Expenses domain repository interfaces."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.shared.kernel.repositories import IRepository

from .entities import Expense, ExpenseCategory


class IExpenseRepository(IRepository[Expense], ABC):
    """Repository interface for Expense operations."""

    @abstractmethod
    async def get_by_id(self, id: UUID, cooperative_id: UUID | None) -> Expense | None:
        pass

    @abstractmethod
    async def get_by_cooperative(self, cooperative_id: UUID) -> list[Expense]:
        pass

    @abstractmethod
    async def add(self, entity: Expense) -> Expense:
        pass

    @abstractmethod
    async def update(self, entity: Expense) -> Expense:
        pass

    @abstractmethod
    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        pass


class IExpenseCategoryRepository(IRepository[ExpenseCategory], ABC):
    """Repository interface for ExpenseCategory operations."""

    @abstractmethod
    async def get_all(self) -> list[ExpenseCategory]:
        pass

    @abstractmethod
    async def get_by_id(self, id: UUID) -> ExpenseCategory | None:
        pass

    @abstractmethod
    async def add(self, entity: ExpenseCategory) -> ExpenseCategory:
        pass

    @abstractmethod
    async def update(self, entity: ExpenseCategory) -> ExpenseCategory:
        pass

    @abstractmethod
    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        pass
