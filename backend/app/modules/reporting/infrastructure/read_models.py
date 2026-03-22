"""Read models and query service for reporting."""

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.reporting.domain.services import CashFlowReport, DebtorInfo


async def debtor_subject_display(session: AsyncSession, subject) -> tuple[dict, str]:
    """Владелец и описание объекта для строки отчёта (subject — ORM FinancialSubject)."""
    from app.modules.land_management.infrastructure.models import (
        LandPlotModel,
        OwnerModel,
        PlotOwnershipModel,
    )
    from app.modules.meters.infrastructure.models import MeterModel

    subject_info: dict = {}
    owner_name = "Неизвестно"

    if subject.subject_type == "LAND_PLOT":
        land_plot_result = await session.execute(
            select(LandPlotModel).where(LandPlotModel.id == subject.subject_id)
        )
        land_plot = land_plot_result.scalar_one_or_none()
        if land_plot:
            subject_info = {
                "plot_number": land_plot.plot_number,
                "area_sqm": str(land_plot.area_sqm),
            }
            ownership_result = await session.execute(
                select(PlotOwnershipModel)
                .where(
                    PlotOwnershipModel.land_plot_id == land_plot.id,
                    PlotOwnershipModel.is_primary,
                )
                .limit(1)
            )
            plot_ownership = ownership_result.scalar_one_or_none()
            if plot_ownership:
                owner_result = await session.execute(
                    select(OwnerModel).where(OwnerModel.id == plot_ownership.owner_id)
                )
                owner = owner_result.scalar_one_or_none()
                if owner:
                    owner_name = owner.name

    elif subject.subject_type in ("WATER_METER", "ELECTRICITY_METER"):
        meter_result = await session.execute(select(MeterModel).where(MeterModel.id == subject.subject_id))
        meter = meter_result.scalar_one_or_none()
        if meter:
            subject_info = {
                "serial_number": meter.serial_number or "N/A",
                "meter_type": meter.meter_type,
            }
            owner_result = await session.execute(select(OwnerModel).where(OwnerModel.id == meter.owner_id))
            owner = owner_result.scalar_one_or_none()
            if owner:
                owner_name = owner.name

    return subject_info, owner_name


class ReportingReadService:
    """Service for reading data from multiple modules for reports."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_debtors_report(
        self,
        cooperative_id: UUID,
        min_debt: Decimal = Decimal("0.00"),
    ) -> list[DebtorInfo]:
        """Generate debtor report for cooperative."""
        # Import models from other modules
        from app.modules.accruals.infrastructure.models import AccrualModel
        from app.modules.financial_core.infrastructure.models import FinancialSubjectModel
        from app.modules.payments.infrastructure.models import PaymentModel

        # Get all financial subjects for cooperative
        result = await self.session.execute(
            select(FinancialSubjectModel).where(
                FinancialSubjectModel.cooperative_id == cooperative_id
            )
        )
        subjects = list(result.scalars().all())

        if not subjects:
            return []

        subject_ids = [s.id for s in subjects]

        # Sum of applied accruals
        accruals_result = await self.session.execute(
            select(AccrualModel.financial_subject_id, func.sum(AccrualModel.amount).label("total"))
            .where(
                AccrualModel.financial_subject_id.in_(subject_ids),
                AccrualModel.status == "applied",
            )
            .group_by(AccrualModel.financial_subject_id)
        )
        accruals_map = {row[0]: row[1] for row in accruals_result.all()}

        # Sum of confirmed payments
        payments_result = await self.session.execute(
            select(PaymentModel.financial_subject_id, func.sum(PaymentModel.amount).label("total"))
            .where(
                PaymentModel.financial_subject_id.in_(subject_ids),
                PaymentModel.status == "confirmed",
            )
            .group_by(PaymentModel.financial_subject_id)
        )
        payments_map = {row[0]: row[1] for row in payments_result.all()}

        # Build result
        debtors = []
        for subject in subjects:
            total_accruals = accruals_map.get(subject.id, Decimal("0.00"))
            total_payments = payments_map.get(subject.id, Decimal("0.00"))
            balance = total_accruals - total_payments

            if balance <= min_debt:
                continue

            subject_info, owner_name = await debtor_subject_display(self.session, subject)

            debtors.append(
                DebtorInfo(
                    financial_subject_id=str(subject.id),
                    subject_type=subject.subject_type,
                    subject_info=subject_info,
                    owner_name=owner_name,
                    total_debt=balance,
                    total_with_penalty=balance,
                )
            )

        debtors.sort(key=lambda d: d.total_debt, reverse=True)
        return debtors

    async def get_debtors_with_penalties(
        self,
        cooperative_id: UUID,
        as_of_date: date,
        min_debt: Decimal,
        debt_repo,
        penalty_settings_repo,
        calculator,
    ) -> list[DebtorInfo]:
        """Должники по активным DebtLine с расчётом пеней на дату."""
        from app.modules.financial_core.application.penalty_use_cases import pick_penalty_settings
        from app.modules.financial_core.infrastructure.models import FinancialSubjectModel

        lines = await debt_repo.get_active_with_outstanding(cooperative_id)
        if not lines:
            return []

        settings_rows = await penalty_settings_repo.list_for_cooperative(cooperative_id)
        grouped: dict[UUID, list] = defaultdict(list)
        for ln in lines:
            grouped[ln.financial_subject_id].append(ln)

        debtors: list[DebtorInfo] = []
        for fs_id, group_lines in grouped.items():
            total_debt = sum((ln.outstanding_amount.amount for ln in group_lines), Decimal("0"))
            if total_debt <= min_debt:
                continue

            penalty_total = Decimal("0.00")
            max_overdue = 0
            for ln in group_lines:
                ps = pick_penalty_settings(settings_rows, ln.contribution_type_id, as_of_date)
                if ps is None:
                    continue
                p = calculator.calculate(ln, ps, as_of_date)
                penalty_total += p.amount
                if ln.due_date is not None:
                    penalty_start = ln.due_date + timedelta(days=ps.grace_period_days + 1)
                    if as_of_date >= penalty_start:
                        max_overdue = max(max_overdue, (as_of_date - penalty_start).days + 1)

            fs_r = await self.session.execute(
                select(FinancialSubjectModel).where(
                    FinancialSubjectModel.id == fs_id,
                    FinancialSubjectModel.cooperative_id == cooperative_id,
                )
            )
            fs_row = fs_r.scalar_one_or_none()
            if fs_row is None:
                continue

            subject_info, owner_name = await debtor_subject_display(self.session, fs_row)
            twp = (total_debt + penalty_total).quantize(Decimal("0.01"))
            debtors.append(
                DebtorInfo(
                    financial_subject_id=str(fs_id),
                    subject_type=fs_row.subject_type,
                    subject_info=subject_info,
                    owner_name=owner_name,
                    total_debt=total_debt,
                    overdue_days=max_overdue,
                    penalty_amount=penalty_total.quantize(Decimal("0.01")),
                    total_with_penalty=twp,
                )
            )

        debtors.sort(key=lambda d: d.total_with_penalty, reverse=True)
        return debtors

    async def get_cash_flow_report(
        self,
        cooperative_id: UUID,
        period_start: date,
        period_end: date,
    ) -> CashFlowReport:
        """Generate cash flow report for period."""
        from app.modules.accruals.infrastructure.models import AccrualModel
        from app.modules.expenses.infrastructure.models import ExpenseModel
        from app.modules.financial_core.infrastructure.models import FinancialSubjectModel
        from app.modules.payments.infrastructure.models import PaymentModel

        # Get all financial subjects for cooperative
        fs_result = await self.session.execute(
            select(FinancialSubjectModel.id).where(
                FinancialSubjectModel.cooperative_id == cooperative_id
            )
        )
        subject_ids = [row[0] for row in fs_result.all()]

        if not subject_ids:
            expenses_result = await self.session.execute(
                select(func.sum(ExpenseModel.amount)).where(
                    ExpenseModel.cooperative_id == cooperative_id,
                    ExpenseModel.status == "confirmed",
                    ExpenseModel.expense_date >= period_start,
                    ExpenseModel.expense_date <= period_end,
                )
            )
            total_expenses = expenses_result.scalar() or Decimal("0.00")
            return CashFlowReport(
                period_start=period_start,
                period_end=period_end,
                total_accruals=Decimal("0.00"),
                total_payments=Decimal("0.00"),
                total_expenses=total_expenses,
                net_balance=Decimal("0.00") - total_expenses,
            )

        # Sum of accruals for period
        accruals_result = await self.session.execute(
            select(func.sum(AccrualModel.amount)).where(
                AccrualModel.financial_subject_id.in_(subject_ids),
                AccrualModel.status == "applied",
                AccrualModel.accrual_date >= period_start,
                AccrualModel.accrual_date <= period_end,
            )
        )
        total_accruals = accruals_result.scalar() or Decimal("0.00")

        # Sum of payments for period
        payments_result = await self.session.execute(
            select(func.sum(PaymentModel.amount)).where(
                PaymentModel.financial_subject_id.in_(subject_ids),
                PaymentModel.status == "confirmed",
                PaymentModel.payment_date >= period_start,
                PaymentModel.payment_date <= period_end,
            )
        )
        total_payments = payments_result.scalar() or Decimal("0.00")

        # Sum of expenses for period
        expenses_result = await self.session.execute(
            select(func.sum(ExpenseModel.amount)).where(
                ExpenseModel.cooperative_id == cooperative_id,
                ExpenseModel.status == "confirmed",
                ExpenseModel.expense_date >= period_start,
                ExpenseModel.expense_date <= period_end,
            )
        )
        total_expenses = expenses_result.scalar() or Decimal("0.00")

        net_balance = total_payments - total_expenses

        return CashFlowReport(
            period_start=period_start,
            period_end=period_end,
            total_accruals=total_accruals,
            total_payments=total_payments,
            total_expenses=total_expenses,
            net_balance=net_balance,
        )
