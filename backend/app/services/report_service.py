from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accrual import Accrual
from app.models.expense import Expense
from app.models.financial_subject import FinancialSubject
from app.models.land_plot import LandPlot
from app.models.meter import Meter
from app.models.owner import Owner
from app.models.payment import Payment
from app.models.plot_ownership import PlotOwnership
from app.schemas.report import CashFlowReport, DebtorInfo


async def get_debtors_report(
    db: AsyncSession,
    cooperative_id: UUID,
    min_debt: Decimal = Decimal("0.00"),
) -> list[DebtorInfo]:
    """
    Отчёт по должникам СТ.

    Выбирает все финансовые субъекты с балансом > min_debt.
    Для каждого субъекта возвращает информацию о владельце и сумму долга.

    :param db: сессия БД
    :param cooperative_id: ID СТ
    :param min_debt: минимальная сумма задолженности для включения в отчёт
    :return: список DebtorInfo
    """
    # Получаем все финансовые субъекты СТ
    result = await db.execute(
        select(FinancialSubject).where(FinancialSubject.cooperative_id == cooperative_id)
    )
    subjects = list(result.scalars().all())

    if not subjects:
        return []

    subject_ids = [s.id for s in subjects]

    # Сумма начислений по всем субъектам (applied)
    accruals_result = await db.execute(
        select(
            Accrual.financial_subject_id,
            func.sum(Accrual.amount).label("total"),
        )
        .where(
            Accrual.financial_subject_id.in_(subject_ids),
            Accrual.status == "applied",
        )
        .group_by(Accrual.financial_subject_id)
    )
    accruals_map = {row[0]: row[1] for row in accruals_result.all()}

    # Сумма платежей по всем субъектам (confirmed)
    payments_result = await db.execute(
        select(
            Payment.financial_subject_id,
            func.sum(Payment.amount).label("total"),
        )
        .where(
            Payment.financial_subject_id.in_(subject_ids),
            Payment.status == "confirmed",
        )
        .group_by(Payment.financial_subject_id)
    )
    payments_map = {row[0]: row[1] for row in payments_result.all()}

    # Формируем результат с фильтрацией по min_debt
    debtors = []
    for subject in subjects:
        total_accruals = accruals_map.get(subject.id, Decimal("0.00"))
        total_payments = payments_map.get(subject.id, Decimal("0.00"))
        balance = total_accruals - total_payments

        if balance <= min_debt:
            continue

        # Получаем информацию о владельце в зависимости от типа субъекта
        subject_info = {}
        owner_name = "Неизвестно"

        if subject.subject_type == "LAND_PLOT":
            # Для участка получаем plot_number и основного владельца
            land_plot_result = await db.execute(
                select(LandPlot).where(LandPlot.id == subject.subject_id)
            )
            land_plot = land_plot_result.scalar_one_or_none()
            if land_plot:
                subject_info = {"plot_number": land_plot.plot_number, "area_sqm": str(land_plot.area_sqm)}

                # Получаем основного владельца (is_primary=True)
                ownership_result = await db.execute(
                    select(PlotOwnership)
                    .where(
                        PlotOwnership.land_plot_id == land_plot.id,
                        PlotOwnership.is_primary == True,
                    )
                    .limit(1)
                )
                plot_ownership = ownership_result.scalar_one_or_none()
                if plot_ownership:
                    owner_result = await db.execute(
                        select(Owner).where(Owner.id == plot_ownership.owner_id)
                    )
                    owner = owner_result.scalar_one_or_none()
                    if owner:
                        owner_name = owner.name

        elif subject.subject_type in ("WATER_METER", "ELECTRICITY_METER"):
            # Для счётчика получаем serial_number и владельца
            meter_result = await db.execute(
                select(Meter).where(Meter.id == subject.subject_id)
            )
            meter = meter_result.scalar_one_or_none()
            if meter:
                subject_info = {"serial_number": meter.serial_number or "N/A", "meter_type": meter.meter_type}

                # Получаем владельца счётчика
                owner_result = await db.execute(
                    select(Owner).where(Owner.id == meter.owner_id)
                )
                owner = owner_result.scalar_one_or_none()
                if owner:
                    owner_name = owner.name

        debtors.append(
            DebtorInfo(
                financial_subject_id=subject.id,
                subject_type=subject.subject_type,
                subject_info=subject_info,
                owner_name=owner_name,
                total_debt=balance,
            )
        )

    # Сортируем по убыванию долга
    debtors.sort(key=lambda d: d.total_debt, reverse=True)

    return debtors


async def get_cash_flow_report(
    db: AsyncSession,
    cooperative_id: UUID,
    period_start: date,
    period_end: date,
) -> CashFlowReport:
    """
    Отчёт о движении денежных средств за период.

    Суммы начислений, платежей и расходов за указанный период.

    :param db: сессия БД
    :param cooperative_id: ID СТ
    :param period_start: начало периода
    :param period_end: конец периода
    :return: CashFlowReport
    """
    # Получаем все финансовые субъекты СТ
    fs_result = await db.execute(
        select(FinancialSubject.id).where(FinancialSubject.cooperative_id == cooperative_id)
    )
    subject_ids = [row[0] for row in fs_result.all()]

    # Сумма начислений за период (по accrual_date, статус applied)
    accruals_result = await db.execute(
        select(func.sum(Accrual.amount)).where(
            Accrual.financial_subject_id.in_(subject_ids) if subject_ids else False,
            Accrual.status == "applied",
            Accrual.accrual_date >= period_start,
            Accrual.accrual_date <= period_end,
        )
    )
    total_accruals = accruals_result.scalar() or Decimal("0.00")

    # Сумма платежей за период (по payment_date, статус confirmed)
    payments_result = await db.execute(
        select(func.sum(Payment.amount)).where(
            Payment.financial_subject_id.in_(subject_ids) if subject_ids else False,
            Payment.status == "confirmed",
            Payment.payment_date >= period_start,
            Payment.payment_date <= period_end,
        )
    )
    total_payments = payments_result.scalar() or Decimal("0.00")

    # Сумма расходов за период (по expense_date, статус confirmed)
    expenses_result = await db.execute(
        select(func.sum(Expense.amount)).where(
            Expense.cooperative_id == cooperative_id,
            Expense.status == "confirmed",
            Expense.expense_date >= period_start,
            Expense.expense_date <= period_end,
        )
    )
    total_expenses = expenses_result.scalar() or Decimal("0.00")

    # Чистый баланс = платежи - расходы
    net_balance = total_payments - total_expenses

    return CashFlowReport(
        period_start=period_start,
        period_end=period_end,
        total_accruals=total_accruals,
        total_payments=total_payments,
        total_expenses=total_expenses,
        net_balance=net_balance,
    )
