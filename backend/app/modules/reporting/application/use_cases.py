"""Use cases for reporting module."""

from datetime import date
from decimal import Decimal
from uuid import UUID


class GenerateDebtorReportUseCase:
    """Use case for generating debtor report."""
    
    def __init__(self, read_service):
        self.read_service = read_service
    
    async def execute(self, cooperative_id: UUID, min_debt: Decimal = Decimal("0.00")):
        """Generate debtor report for cooperative."""
        return await self.read_service.get_debtors_report(cooperative_id, min_debt)


class GenerateCashFlowUseCase:
    """Use case for generating cash flow report."""
    
    def __init__(self, read_service):
        self.read_service = read_service
    
    async def execute(self, cooperative_id: UUID, period_start: date, period_end: date):
        """Generate cash flow report for period."""
        return await self.read_service.get_cash_flow_report(cooperative_id, period_start, period_end)
