"""Dependency injection for Clean Architecture modules.

This module provides dependency injection containers for each module,
ensuring proper separation of concerns and testability.
"""

from typing import Protocol

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db


class SessionDep(Protocol):
    """Protocol for database session dependency."""

    def __call__(self, db: AsyncSession = Depends(get_db)) -> AsyncSession:
        ...


# =============================================================================
# Shared Kernel Dependencies
# =============================================================================

def get_event_dispatcher():
    """Get global event dispatcher instance."""
    from app.modules.shared.kernel.events import EventDispatcher
    return EventDispatcher()


# =============================================================================
# Cooperative Core Dependencies (base dependency for other modules)
# =============================================================================

def get_cooperative_repository(db: AsyncSession = Depends(get_db)):
    """Get CooperativeRepository instance."""
    from app.modules.cooperative_core.infrastructure.repositories import CooperativeRepository
    return CooperativeRepository(db)


# =============================================================================
# Financial Core Dependencies (needed by other modules)
# =============================================================================

def get_financial_subject_repository(db: AsyncSession = Depends(get_db)):
    """Get FinancialSubjectRepository instance."""
    from app.modules.financial_core.infrastructure.repositories import FinancialSubjectRepository
    return FinancialSubjectRepository(db)


def get_balance_repository(db: AsyncSession = Depends(get_db)):
    """Get BalanceRepository instance."""
    from app.modules.financial_core.infrastructure.repositories import BalanceRepository
    return BalanceRepository(db)


def get_get_financial_subject_use_case(fs_repo=Depends(get_financial_subject_repository)):
    """Get GetFinancialSubjectUseCase instance."""
    from app.modules.financial_core.application.use_cases import GetFinancialSubjectUseCase
    return GetFinancialSubjectUseCase(fs_repo)


def get_get_financial_subjects_use_case(fs_repo=Depends(get_financial_subject_repository)):
    """Get GetFinancialSubjectsUseCase instance."""
    from app.modules.financial_core.application.use_cases import GetFinancialSubjectsUseCase
    return GetFinancialSubjectsUseCase(fs_repo)


def get_get_balance_use_case(balance_repo=Depends(get_balance_repository)):
    """Get GetBalanceUseCase instance."""
    from app.modules.financial_core.application.use_cases import GetBalanceUseCase
    return GetBalanceUseCase(balance_repo)


def get_get_balances_by_cooperative_use_case(balance_repo=Depends(get_balance_repository)):
    """Get GetBalancesByCooperativeUseCase instance."""
    from app.modules.financial_core.application.use_cases import GetBalancesByCooperativeUseCase
    return GetBalancesByCooperativeUseCase(balance_repo)


# =============================================================================
# Land Management Dependencies
# =============================================================================

def get_land_plot_repository(db: AsyncSession = Depends(get_db)):
    """Get LandPlotRepository instance."""
    from app.modules.land_management.infrastructure.repositories import LandPlotRepository
    return LandPlotRepository(db)


def get_owner_repository(db: AsyncSession = Depends(get_db)):
    """Get OwnerRepository instance."""
    from app.modules.land_management.infrastructure.repositories import OwnerRepository
    return OwnerRepository(db)


def get_plot_ownership_repository(db: AsyncSession = Depends(get_db)):
    """Get PlotOwnershipRepository instance."""
    from app.modules.land_management.infrastructure.repositories import PlotOwnershipRepository
    return PlotOwnershipRepository(db)


def get_create_land_plot_use_case(
    land_plot_repo=Depends(get_land_plot_repository),
    ownership_repo=Depends(get_plot_ownership_repository),
    fs_repo=Depends(get_financial_subject_repository),
    event_dispatcher=Depends(get_event_dispatcher),
):
    """Get CreateLandPlotUseCase instance."""
    from app.modules.land_management.application.use_cases import CreateLandPlotUseCase
    return CreateLandPlotUseCase(land_plot_repo, ownership_repo, fs_repo, event_dispatcher)


def get_get_land_plot_use_case(land_plot_repo=Depends(get_land_plot_repository)):
    """Get GetLandPlotUseCase instance."""
    from app.modules.land_management.application.use_cases import GetLandPlotUseCase
    return GetLandPlotUseCase(land_plot_repo)


def get_get_land_plots_use_case(land_plot_repo=Depends(get_land_plot_repository)):
    """Get GetLandPlotsUseCase instance."""
    from app.modules.land_management.application.use_cases import GetLandPlotsUseCase
    return GetLandPlotsUseCase(land_plot_repo)


def get_update_land_plot_use_case(land_plot_repo=Depends(get_land_plot_repository)):
    """Get UpdateLandPlotUseCase instance."""
    from app.modules.land_management.application.use_cases import UpdateLandPlotUseCase
    return UpdateLandPlotUseCase(land_plot_repo)


def get_delete_land_plot_use_case(land_plot_repo=Depends(get_land_plot_repository)):
    """Get DeleteLandPlotUseCase instance."""
    from app.modules.land_management.application.use_cases import DeleteLandPlotUseCase
    return DeleteLandPlotUseCase(land_plot_repo)


def get_create_owner_use_case(
    owner_repo=Depends(get_owner_repository),
    event_dispatcher=Depends(get_event_dispatcher),
):
    """Get CreateOwnerUseCase instance."""
    from app.modules.land_management.application.use_cases import CreateOwnerUseCase
    return CreateOwnerUseCase(owner_repo, event_dispatcher)


def get_get_owner_use_case(owner_repo=Depends(get_owner_repository)):
    """Get GetOwnerUseCase instance."""
    from app.modules.land_management.application.use_cases import GetOwnerUseCase
    return GetOwnerUseCase(owner_repo)


def get_get_owners_use_case(owner_repo=Depends(get_owner_repository)):
    """Get GetOwnersUseCase instance."""
    from app.modules.land_management.application.use_cases import GetOwnersUseCase
    return GetOwnersUseCase(owner_repo)


def get_update_owner_use_case(owner_repo=Depends(get_owner_repository)):
    """Get UpdateOwnerUseCase instance."""
    from app.modules.land_management.application.use_cases import UpdateOwnerUseCase
    return UpdateOwnerUseCase(owner_repo)


def get_delete_owner_use_case(owner_repo=Depends(get_owner_repository)):
    """Get DeleteOwnerUseCase instance."""
    from app.modules.land_management.application.use_cases import DeleteOwnerUseCase
    return DeleteOwnerUseCase(owner_repo)


def get_search_owners_use_case(owner_repo=Depends(get_owner_repository)):
    """Get SearchOwnersUseCase instance."""
    from app.modules.land_management.application.use_cases import SearchOwnersUseCase
    return SearchOwnersUseCase(owner_repo)


def get_create_plot_ownership_use_case(
    ownership_repo=Depends(get_plot_ownership_repository),
    land_plot_repo=Depends(get_land_plot_repository),
    event_dispatcher=Depends(get_event_dispatcher),
):
    """Get CreatePlotOwnershipUseCase instance."""
    from app.modules.land_management.application.use_cases import CreatePlotOwnershipUseCase
    return CreatePlotOwnershipUseCase(ownership_repo, land_plot_repo, event_dispatcher)


def get_close_plot_ownership_use_case(
    ownership_repo=Depends(get_plot_ownership_repository),
    event_dispatcher=Depends(get_event_dispatcher),
):
    """Get ClosePlotOwnershipUseCase instance."""
    from app.modules.land_management.application.use_cases import ClosePlotOwnershipUseCase
    return ClosePlotOwnershipUseCase(ownership_repo, event_dispatcher)


def get_plot_ownership_use_case(ownership_repo=Depends(get_plot_ownership_repository)):
    """Get GetPlotOwnershipUseCase instance."""
    from app.modules.land_management.application.use_cases import GetPlotOwnershipUseCase
    return GetPlotOwnershipUseCase(ownership_repo)


def get_current_plot_ownerships_use_case(ownership_repo=Depends(get_plot_ownership_repository)):
    """Get GetCurrentPlotOwnershipsUseCase instance."""
    from app.modules.land_management.application.use_cases import GetCurrentPlotOwnershipsUseCase
    return GetCurrentPlotOwnershipsUseCase(ownership_repo)


# =============================================================================
# Accruals Dependencies
# =============================================================================

def get_accrual_repository(db: AsyncSession = Depends(get_db)):
    """Get AccrualRepository instance."""
    from app.modules.accruals.infrastructure.repositories import AccrualRepository
    return AccrualRepository(db)


def get_contribution_type_repository(db: AsyncSession = Depends(get_db)):
    """Get ContributionTypeRepository instance."""
    from app.modules.accruals.infrastructure.repositories import ContributionTypeRepository
    return ContributionTypeRepository(db)


def get_create_accrual_use_case(
    accrual_repo=Depends(get_accrual_repository),
    fs_repo=Depends(get_financial_subject_repository),
):
    """Get CreateAccrualUseCase instance."""
    from app.modules.accruals.application.use_cases import CreateAccrualUseCase
    return CreateAccrualUseCase(accrual_repo, fs_repo)


def get_get_accrual_use_case(accrual_repo=Depends(get_accrual_repository)):
    """Get GetAccrualUseCase instance."""
    from app.modules.accruals.application.use_cases import GetAccrualUseCase
    return GetAccrualUseCase(accrual_repo)


def get_accruals_by_financial_subject_use_case(accrual_repo=Depends(get_accrual_repository)):
    """Get GetAccrualsByFinancialSubjectUseCase instance."""
    from app.modules.accruals.application.use_cases import GetAccrualsByFinancialSubjectUseCase
    return GetAccrualsByFinancialSubjectUseCase(accrual_repo)


def get_accruals_by_cooperative_use_case(accrual_repo=Depends(get_accrual_repository)):
    """Get GetAccrualsByCooperativeUseCase instance."""
    from app.modules.accruals.application.use_cases import GetAccrualsByCooperativeUseCase
    return GetAccrualsByCooperativeUseCase(accrual_repo)


def get_apply_accrual_use_case(
    accrual_repo=Depends(get_accrual_repository),
    fs_repo=Depends(get_financial_subject_repository),
    balance_repo=Depends(get_balance_repository),
):
    """Get ApplyAccrualUseCase instance."""
    from app.modules.accruals.application.use_cases import ApplyAccrualUseCase
    return ApplyAccrualUseCase(accrual_repo, fs_repo, balance_repo)


def get_cancel_accrual_use_case(
    accrual_repo=Depends(get_accrual_repository),
    fs_repo=Depends(get_financial_subject_repository),
    balance_repo=Depends(get_balance_repository),
):
    """Get CancelAccrualUseCase instance."""
    from app.modules.accruals.application.use_cases import CancelAccrualUseCase
    return CancelAccrualUseCase(accrual_repo, fs_repo, balance_repo)


def get_mass_create_accruals_use_case(
    accrual_repo=Depends(get_accrual_repository),
    fs_repo=Depends(get_financial_subject_repository),
):
    """Get MassCreateAccrualsUseCase instance."""
    from app.modules.accruals.application.use_cases import MassCreateAccrualsUseCase
    return MassCreateAccrualsUseCase(accrual_repo, fs_repo)


def get_get_contribution_types_use_case(ct_repo=Depends(get_contribution_type_repository)):
    """Get GetContributionTypesUseCase instance."""
    from app.modules.accruals.application.use_cases import GetContributionTypesUseCase
    return GetContributionTypesUseCase(ct_repo)


# =============================================================================
# Payments Dependencies
# =============================================================================

def get_payment_repository(db: AsyncSession = Depends(get_db)):
    """Get PaymentRepository instance."""
    from app.modules.payments.infrastructure.repositories import PaymentRepository
    return PaymentRepository(db)


def get_register_payment_use_case(
    payment_repo=Depends(get_payment_repository),
    fs_repo=Depends(get_financial_subject_repository),
    balance_repo=Depends(get_balance_repository),
):
    """Get RegisterPaymentUseCase instance."""
    from app.modules.payments.application.use_cases import RegisterPaymentUseCase
    return RegisterPaymentUseCase(payment_repo, fs_repo, balance_repo)


def get_get_payment_use_case(payment_repo=Depends(get_payment_repository)):
    """Get GetPaymentUseCase instance."""
    from app.modules.payments.application.use_cases import GetPaymentUseCase
    return GetPaymentUseCase(payment_repo)


def get_payments_by_financial_subject_use_case(payment_repo=Depends(get_payment_repository)):
    """Get GetPaymentsByFinancialSubjectUseCase instance."""
    from app.modules.payments.application.use_cases import GetPaymentsByFinancialSubjectUseCase
    return GetPaymentsByFinancialSubjectUseCase(payment_repo)


def get_payments_by_owner_use_case(payment_repo=Depends(get_payment_repository)):
    """Get GetPaymentsByOwnerUseCase instance."""
    from app.modules.payments.application.use_cases import GetPaymentsByOwnerUseCase
    return GetPaymentsByOwnerUseCase(payment_repo)


def get_payments_by_cooperative_use_case(payment_repo=Depends(get_payment_repository)):
    """Get GetPaymentsByCooperativeUseCase instance."""
    from app.modules.payments.application.use_cases import GetPaymentsByCooperativeUseCase
    return GetPaymentsByCooperativeUseCase(payment_repo)


def get_cancel_payment_use_case(
    payment_repo=Depends(get_payment_repository),
    fs_repo=Depends(get_financial_subject_repository),
    balance_repo=Depends(get_balance_repository),
):
    """Get CancelPaymentUseCase instance."""
    from app.modules.payments.application.use_cases import CancelPaymentUseCase
    return CancelPaymentUseCase(payment_repo, fs_repo, balance_repo)


# =============================================================================
# Meters Dependencies
# =============================================================================

def get_meter_repository(db: AsyncSession = Depends(get_db)):
    """Get MeterRepository instance."""
    from app.modules.meters.infrastructure.repositories import MeterRepository
    return MeterRepository(db)


def get_meter_reading_repository(db: AsyncSession = Depends(get_db)):
    """Get MeterReadingRepository instance."""
    from app.modules.meters.infrastructure.repositories import MeterReadingRepository
    return MeterReadingRepository(db)


def get_create_meter_use_case(
    meter_repo=Depends(get_meter_repository),
    fs_repo=Depends(get_financial_subject_repository),
    event_dispatcher=Depends(get_event_dispatcher),
):
    """Get CreateMeterUseCase instance."""
    from app.modules.meters.application.use_cases import CreateMeterUseCase
    return CreateMeterUseCase(meter_repo, fs_repo, event_dispatcher)


def get_get_meter_use_case(meter_repo=Depends(get_meter_repository)):
    """Get GetMeterUseCase instance."""
    from app.modules.meters.application.use_cases import GetMeterUseCase
    return GetMeterUseCase(meter_repo)


def get_meters_by_owner_use_case(meter_repo=Depends(get_meter_repository)):
    """Get GetMetersByOwnerUseCase instance."""
    from app.modules.meters.application.use_cases import GetMetersByOwnerUseCase
    return GetMetersByOwnerUseCase(meter_repo)


def get_update_meter_use_case(meter_repo=Depends(get_meter_repository)):
    """Get UpdateMeterUseCase instance."""
    from app.modules.meters.application.use_cases import UpdateMeterUseCase
    return UpdateMeterUseCase(meter_repo)


def get_delete_meter_use_case(meter_repo=Depends(get_meter_repository)):
    """Get DeleteMeterUseCase instance."""
    from app.modules.meters.application.use_cases import DeleteMeterUseCase
    return DeleteMeterUseCase(meter_repo)


def get_add_meter_reading_use_case(
    reading_repo=Depends(get_meter_reading_repository),
    meter_repo=Depends(get_meter_repository),
):
    """Get AddMeterReadingUseCase instance."""
    from app.modules.meters.application.use_cases import AddMeterReadingUseCase
    return AddMeterReadingUseCase(reading_repo, meter_repo)


def get_meter_readings_use_case(reading_repo=Depends(get_meter_reading_repository)):
    """Get GetMeterReadingsUseCase instance."""
    from app.modules.meters.application.use_cases import GetMeterReadingsUseCase
    return GetMeterReadingsUseCase(reading_repo)


# =============================================================================
# Expenses Dependencies
# =============================================================================

def get_expense_repository(db: AsyncSession = Depends(get_db)):
    """Get ExpenseRepository instance."""
    from app.modules.expenses.infrastructure.repositories import ExpenseRepository
    return ExpenseRepository(db)


def get_expense_category_repository(db: AsyncSession = Depends(get_db)):
    """Get ExpenseCategoryRepository instance."""
    from app.modules.expenses.infrastructure.repositories import ExpenseCategoryRepository
    return ExpenseCategoryRepository(db)


def get_create_expense_use_case(
    expense_repo=Depends(get_expense_repository),
    fs_repo=Depends(get_financial_subject_repository),
):
    """Get CreateExpenseUseCase instance."""
    from app.modules.expenses.application.use_cases import CreateExpenseUseCase
    return CreateExpenseUseCase(expense_repo, fs_repo)


def get_get_expense_use_case(expense_repo=Depends(get_expense_repository)):
    """Get GetExpenseUseCase instance."""
    from app.modules.expenses.application.use_cases import GetExpenseUseCase
    return GetExpenseUseCase(expense_repo)


def get_expenses_by_cooperative_use_case(expense_repo=Depends(get_expense_repository)):
    """Get GetExpensesByCooperativeUseCase instance."""
    from app.modules.expenses.application.use_cases import GetExpensesByCooperativeUseCase
    return GetExpensesByCooperativeUseCase(expense_repo)


def get_confirm_expense_use_case(
    expense_repo=Depends(get_expense_repository),
    fs_repo=Depends(get_financial_subject_repository),
    balance_repo=Depends(get_balance_repository),
):
    """Get ConfirmExpenseUseCase instance."""
    from app.modules.expenses.application.use_cases import ConfirmExpenseUseCase
    return ConfirmExpenseUseCase(expense_repo, fs_repo, balance_repo)


def get_cancel_expense_use_case(
    expense_repo=Depends(get_expense_repository),
    fs_repo=Depends(get_financial_subject_repository),
    balance_repo=Depends(get_balance_repository),
):
    """Get CancelExpenseUseCase instance."""
    from app.modules.expenses.application.use_cases import CancelExpenseUseCase
    return CancelExpenseUseCase(expense_repo, fs_repo, balance_repo)


def get_expense_categories_use_case(cat_repo=Depends(get_expense_category_repository)):
    """Get GetExpenseCategoriesUseCase instance."""
    from app.modules.expenses.application.use_cases import GetExpenseCategoriesUseCase
    return GetExpenseCategoriesUseCase(cat_repo)


# =============================================================================
# Reporting Dependencies
# =============================================================================

def get_reporting_read_service(db: AsyncSession = Depends(get_db)):
    """Get ReportingReadService instance."""
    from app.modules.reporting.infrastructure.read_models import ReportingReadService
    return ReportingReadService(db)


# =============================================================================
# Administration Dependencies
# =============================================================================

def get_app_user_repository(db: AsyncSession = Depends(get_db)):
    """Get AppUserRepository instance."""
    from app.modules.administration.infrastructure.repositories import AppUserRepository
    return AppUserRepository(db)
