"""Legacy models module - re-exports from Clean Architecture modules.

This module provides backward compatibility by re-exporting models
from the new Clean Architecture modules.

DEPRECATED: Use app.modules.*.infrastructure.models instead.
"""

# Re-export from Clean Architecture modules to maintain backward compatibility
from app.modules.accruals.infrastructure.models import AccrualModel as Accrual
from app.modules.accruals.infrastructure.models import ContributionTypeModel as ContributionType
from app.modules.administration.infrastructure.models import AppUserModel as AppUser
from app.modules.cooperative_core.infrastructure.models import CooperativeModel as Cooperative
from app.modules.expenses.infrastructure.models import ExpenseCategoryModel as ExpenseCategory
from app.modules.expenses.infrastructure.models import ExpenseModel as Expense
from app.modules.financial_core.infrastructure.models import FinancialSubjectModel as FinancialSubject
from app.modules.land_management.infrastructure.models import LandPlotModel as LandPlot
from app.modules.land_management.infrastructure.models import OwnerModel as Owner
from app.modules.land_management.infrastructure.models import PlotOwnershipModel as PlotOwnership
from app.modules.meters.infrastructure.models import MeterModel as Meter
from app.modules.meters.infrastructure.models import MeterReadingModel as MeterReading
from app.modules.payments.infrastructure.models import PaymentModel as Payment

__all__ = [
    "Accrual",
    "ContributionType",
    "AppUser",
    "Cooperative",
    "ExpenseCategory",
    "Expense",
    "FinancialSubject",
    "LandPlot",
    "Owner",
    "PlotOwnership",
    "Meter",
    "MeterReading",
    "Payment",
]
