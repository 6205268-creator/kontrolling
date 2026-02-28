"""Expenses repository implementations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.expenses.domain.entities import Expense, ExpenseCategory
from app.modules.expenses.domain.repositories import IExpenseRepository, IExpenseCategoryRepository

from .models import ExpenseModel, ExpenseCategoryModel


class ExpenseRepository(IExpenseRepository):
    """SQLAlchemy implementation of Expense repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> Expense | None:
        """Get expense by ID, filtered by cooperative."""
        query = select(ExpenseModel).where(
            ExpenseModel.id == id,
            ExpenseModel.cooperative_id == cooperative_id,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_cooperative(self, cooperative_id: UUID) -> list[Expense]:
        """Get all expenses for a cooperative."""
        query = (
            select(ExpenseModel)
            .where(ExpenseModel.cooperative_id == cooperative_id)
            .order_by(ExpenseModel.expense_date.desc())
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def add(self, entity: Expense) -> Expense:
        """Add new expense."""
        model = ExpenseModel.from_domain(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def update(self, entity: Expense) -> Expense:
        """Update existing expense."""
        query = select(ExpenseModel).where(ExpenseModel.id == entity.id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Expense with id {entity.id} not found")
        
        model.category_id = entity.category_id
        model.amount = entity.amount
        model.expense_date = entity.expense_date
        model.document_number = entity.document_number
        model.description = entity.description
        model.status = entity.status
        
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()

    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete expense by ID."""
        query = select(ExpenseModel).where(
            ExpenseModel.id == id,
            ExpenseModel.cooperative_id == cooperative_id,
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.commit()


class ExpenseCategoryRepository(IExpenseCategoryRepository):
    """SQLAlchemy implementation of ExpenseCategory repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, cooperative_id: UUID) -> list[ExpenseCategory]:
        """Get all expense categories."""
        query = select(ExpenseCategoryModel).order_by(ExpenseCategoryModel.name)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> ExpenseCategory | None:
        """Get expense category by ID."""
        query = select(ExpenseCategoryModel).where(ExpenseCategoryModel.id == id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def add(self, entity: ExpenseCategory) -> ExpenseCategory:
        """Add new expense category."""
        model = ExpenseCategoryModel.from_domain(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_domain()
