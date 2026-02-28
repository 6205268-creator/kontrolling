"""ExpenseCategory model - re-export from Clean Architecture modules."""
from app.modules.expenses.infrastructure.models import ExpenseCategoryModel as ExpenseCategory

__all__ = ["ExpenseCategory"]
