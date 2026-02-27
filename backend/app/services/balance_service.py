from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accrual import Accrual
from app.models.financial_subject import FinancialSubject
from app.models.payment import Payment
from app.schemas.balance import BalanceInfo


async def calculate_balance(
    db: AsyncSession,
    financial_subject_id: UUID,
) -> BalanceInfo | None:
    """
    Расчёт баланса финансового субъекта.

    balance = total_accruals (applied) - total_payments (confirmed)

    Возвращает BalanceInfo или None если субъект не найден.
    """
    # Получаем финансовый субъект
    result = await db.execute(
        select(FinancialSubject).where(FinancialSubject.id == financial_subject_id)
    )
    subject = result.scalar_one_or_none()
    if subject is None:
        return None

    # Сумма начислений со статусом "applied"
    accruals_result = await db.execute(
        select(func.sum(Accrual.amount)).where(
            Accrual.financial_subject_id == financial_subject_id,
            Accrual.status == "applied",
        )
    )
    total_accruals = accruals_result.scalar() or Decimal("0.00")

    # Сумма платежей со статусом "confirmed"
    payments_result = await db.execute(
        select(func.sum(Payment.amount)).where(
            Payment.financial_subject_id == financial_subject_id,
            Payment.status == "confirmed",
        )
    )
    total_payments = payments_result.scalar() or Decimal("0.00")

    return BalanceInfo(
        financial_subject_id=financial_subject_id,
        subject_type=subject.subject_type,
        subject_id=subject.subject_id,
        cooperative_id=subject.cooperative_id,
        code=subject.code,
        total_accruals=total_accruals,
        total_payments=total_payments,
        balance=total_accruals - total_payments,
    )


async def get_balances_by_cooperative(
    db: AsyncSession,
    cooperative_id: UUID,
) -> list[BalanceInfo]:
    """
    Получение балансов всех финансовых субъектов СТ.

    Возвращает список BalanceInfo для всех субъектов указанного СТ.
    """
    # Получаем все финансовые субъекты СТ
    result = await db.execute(
        select(FinancialSubject).where(FinancialSubject.cooperative_id == cooperative_id)
    )
    subjects = list(result.scalars().all())

    # Если нет субъектов, возвращаем пустой список
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

    # Формируем результат
    balances = []
    for subject in subjects:
        total_accruals = accruals_map.get(subject.id, Decimal("0.00"))
        total_payments = payments_map.get(subject.id, Decimal("0.00"))
        balances.append(
            BalanceInfo(
                financial_subject_id=subject.id,
                subject_type=subject.subject_type,
                subject_id=subject.subject_id,
                cooperative_id=subject.cooperative_id,
                code=subject.code,
                total_accruals=total_accruals,
                total_payments=total_payments,
                balance=total_accruals - total_payments,
            )
        )

    return balances


async def get_financial_subjects_by_cooperative(
    db: AsyncSession,
    cooperative_id: UUID,
) -> list[FinancialSubject]:
    """Получение списка финансовых субъектов по СТ."""
    result = await db.execute(
        select(FinancialSubject).where(FinancialSubject.cooperative_id == cooperative_id)
    )
    return list(result.scalars().all())


async def get_financial_subject(db: AsyncSession, subject_id: UUID) -> FinancialSubject | None:
    """Получение финансового субъекта по ID."""
    result = await db.execute(
        select(FinancialSubject).where(FinancialSubject.id == subject_id)
    )
    return result.scalar_one_or_none()
