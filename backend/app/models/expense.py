"""Expense model - re-export from Clean Architecture modules."""
from app.modules.expenses.infrastructure.models import ExpenseModel as Expense

__all__ = ["Expense"]
