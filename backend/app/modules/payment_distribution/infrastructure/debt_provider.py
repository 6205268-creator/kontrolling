"""DebtProvider — provides debt data for payment distribution.

This module provides the DebtProvider class which implements the interface
for getting member's debts (outstanding accruals) sorted by priority.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.shared.kernel.money import Money


@dataclass
class DebtInfo:
    """Information about a debt for distribution purposes."""

    financial_subject_id: UUID
    accrual_id: UUID
    balance: Money
    priority: int
    description: str
    due_date: date | None = None


class DebtProvider:
    """Provides debt information for payment distribution.

    Fetches outstanding accruals for member's financial subjects,
    sorted by priority (oldest first).
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_member_debts(
        self,
        owner_id: UUID,
        cooperative_id: UUID,
    ) -> list[DebtInfo]:
        """Get member's debts sorted by priority.

        Priority is determined by:
        1. due_date (earlier due date = higher priority)
        2. accrual_date (older accrual = higher priority)

        Args:
            owner_id: ID of the owner.
            cooperative_id: ID of the cooperative.

        Returns:
            List of DebtInfo objects sorted by priority (ascending).
        """
        from app.modules.accruals.infrastructure.models import AccrualModel
        from app.modules.financial_core.infrastructure.models import FinancialSubjectModel
        from app.modules.land_management.infrastructure.models import (
            LandPlotModel,
            PlotOwnershipModel,
        )

        # Get all financial subjects for member's plots
        # Join: Owner -> PlotOwnership -> LandPlot -> FinancialSubject
        query = (
            select(
                AccrualModel.id,
                AccrualModel.financial_subject_id,
                AccrualModel.amount,
                AccrualModel.accrual_date,
                AccrualModel.due_date,
                FinancialSubjectModel.subject_type,
                FinancialSubjectModel.code,
                LandPlotModel.plot_number,
            )
            .join(
                FinancialSubjectModel,
                AccrualModel.financial_subject_id == FinancialSubjectModel.id,
            )
            .join(
                LandPlotModel,
                FinancialSubjectModel.subject_id == LandPlotModel.id,
            )
            .join(
                PlotOwnershipModel,
                LandPlotModel.id == PlotOwnershipModel.land_plot_id,
            )
            .where(
                PlotOwnershipModel.owner_id == owner_id,
                PlotOwnershipModel.is_primary == True,  # noqa: E712
                LandPlotModel.cooperative_id == cooperative_id,
                AccrualModel.status == "applied",
            )
            .order_by(
                AccrualModel.due_date.asc().nullsfirst(),
                AccrualModel.accrual_date.asc(),
            )
        )

        result = await self.session.execute(query)
        rows = result.all()

        # Get paid amounts from payment_distributions
        accrual_ids = [row[0] for row in rows]
        if not accrual_ids:
            return []

        from sqlalchemy import func

        from app.modules.payment_distribution.infrastructure.models import (
            PaymentDistributionModel,
        )

        paid_query = (
            select(
                PaymentDistributionModel.accrual_id,
                select(func.sum(PaymentDistributionModel.amount))
                .where(
                    PaymentDistributionModel.accrual_id == PaymentDistributionModel.accrual_id,
                    PaymentDistributionModel.status == "applied",
                )
                .correlate(PaymentDistributionModel)
                .scalar_subquery()
                .label("paid_amount"),
            )
            .where(PaymentDistributionModel.accrual_id.in_(accrual_ids))
            .group_by(PaymentDistributionModel.accrual_id)
        )

        from sqlalchemy import func

        paid_result = await self.session.execute(paid_query)
        paid_map = {row[0]: row[1] or Decimal("0") for row in paid_result.all()}

        # Build debt list
        debts = []
        priority = 0
        for row in rows:
            accrual_id, fs_id, amount, accrual_date, due_date, subject_type, code, plot_number = row

            # Calculate outstanding balance
            paid_amount = paid_map.get(accrual_id, Decimal("0"))
            outstanding = amount - paid_amount

            # Skip fully paid accruals
            if outstanding <= 0:
                continue

            priority += 1
            debts.append(
                DebtInfo(
                    financial_subject_id=fs_id,
                    accrual_id=accrual_id,
                    balance=Money(outstanding),
                    priority=priority,
                    description=f"{code} ({plot_number}) за {accrual_date.strftime('%Y-%m')}",
                    due_date=due_date,
                )
            )

        return debts
