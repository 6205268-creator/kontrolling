from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.schemas.payment import PaymentCreate


async def register_payment(db: AsyncSession, payment_data: PaymentCreate) -> Payment:
    """
    Регистрация платежа.

    При создании статус = "confirmed".
    """
    db_payment = Payment(
        financial_subject_id=payment_data.financial_subject_id,
        payer_owner_id=payment_data.payer_owner_id,
        amount=payment_data.amount,
        payment_date=payment_data.payment_date,
        document_number=payment_data.document_number,
        description=payment_data.description,
        status="confirmed",
    )
    db.add(db_payment)
    await db.commit()
    await db.refresh(db_payment)
    return db_payment


async def get_payment(db: AsyncSession, payment_id: UUID) -> Payment | None:
    """Получение платежа по ID."""
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    return result.scalar_one_or_none()


async def cancel_payment(db: AsyncSession, payment_id: UUID) -> Payment:
    """
    Отмена платежа (смена статуса на "cancelled").

    Отменяется платёж со статусом "confirmed".
    """
    payment = await get_payment(db, payment_id)
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Платёж не найден",
        )

    if payment.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Платёж уже отменён",
        )

    payment.status = "cancelled"
    await db.commit()
    await db.refresh(payment)
    return payment


async def get_payments_by_financial_subject(
    db: AsyncSession,
    financial_subject_id: UUID,
) -> list[Payment]:
    """Получение списка платежей по финансовому субъекту."""
    result = await db.execute(
        select(Payment)
        .where(Payment.financial_subject_id == financial_subject_id)
        .order_by(Payment.payment_date.desc())
    )
    return list(result.scalars().all())


async def get_payments_by_owner(
    db: AsyncSession,
    owner_id: UUID,
) -> list[Payment]:
    """Получение списка платежей владельца."""
    result = await db.execute(
        select(Payment)
        .where(Payment.payer_owner_id == owner_id)
        .order_by(Payment.payment_date.desc())
    )
    return list(result.scalars().all())


async def get_payments_by_cooperative(
    db: AsyncSession,
    cooperative_id: UUID,
) -> list[Payment]:
    """Получение списка платежей по СТ (через FinancialSubject)."""
    from app.models.financial_subject import FinancialSubject

    result = await db.execute(
        select(Payment)
        .join(FinancialSubject, Payment.financial_subject_id == FinancialSubject.id)
        .where(FinancialSubject.cooperative_id == cooperative_id)
        .order_by(Payment.payment_date.desc())
    )
    return list(result.scalars().all())
