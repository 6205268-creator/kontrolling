from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accrual import Accrual
from app.schemas.accrual import AccrualCreate


async def create_accrual(db: AsyncSession, accrual_data: AccrualCreate) -> Accrual:
    """
    Создание начисления.

    При создании статус = "created".
    """
    db_accrual = Accrual(
        financial_subject_id=accrual_data.financial_subject_id,
        contribution_type_id=accrual_data.contribution_type_id,
        amount=accrual_data.amount,
        accrual_date=accrual_data.accrual_date,
        period_start=accrual_data.period_start,
        period_end=accrual_data.period_end,
        status="created",
    )
    db.add(db_accrual)
    await db.commit()
    await db.refresh(db_accrual)
    return db_accrual


async def get_accrual(db: AsyncSession, accrual_id: UUID) -> Accrual | None:
    """Получение начисления по ID."""
    result = await db.execute(select(Accrual).where(Accrual.id == accrual_id))
    return result.scalar_one_or_none()


async def apply_accrual(db: AsyncSession, accrual_id: UUID) -> Accrual:
    """
    Применение начисления (смена статуса на "applied").

    Применяется только начисление со статусом "created".
    """
    accrual = await get_accrual(db, accrual_id)
    if accrual is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Начисление не найдено",
        )

    if accrual.status != "created":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Нельзя применить начисление со статусом '{accrual.status}'. Только статус 'created'.",
        )

    accrual.status = "applied"
    await db.commit()
    await db.refresh(accrual)
    return accrual


async def cancel_accrual(db: AsyncSession, accrual_id: UUID) -> Accrual:
    """
    Отмена начисления (смена статуса на "cancelled").

    Отменяется начисление со статусом "created" или "applied".
    """
    accrual = await get_accrual(db, accrual_id)
    if accrual is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Начисление не найдено",
        )

    if accrual.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Начисление уже отменено",
        )

    accrual.status = "cancelled"
    await db.commit()
    await db.refresh(accrual)
    return accrual


async def get_accruals_by_financial_subject(
    db: AsyncSession,
    financial_subject_id: UUID,
) -> list[Accrual]:
    """Получение списка начислений по финансовому субъекту."""
    result = await db.execute(
        select(Accrual)
        .where(Accrual.financial_subject_id == financial_subject_id)
        .order_by(Accrual.accrual_date.desc())
    )
    return list(result.scalars().all())


async def get_accruals_by_cooperative(
    db: AsyncSession,
    cooperative_id: UUID,
) -> list[Accrual]:
    """Получение списка начислений по СТ (через FinancialSubject)."""
    from app.models.financial_subject import FinancialSubject

    result = await db.execute(
        select(Accrual)
        .join(FinancialSubject, Accrual.financial_subject_id == FinancialSubject.id)
        .where(FinancialSubject.cooperative_id == cooperative_id)
        .order_by(Accrual.accrual_date.desc())
    )
    return list(result.scalars().all())


async def mass_create_accruals(
    db: AsyncSession,
    accruals_data: list[AccrualCreate],
) -> list[Accrual]:
    """
    Массовое создание начислений.

    Все начисления создаются в одной транзакции со статусом "created".
    """
    if not accruals_data:
        return []

    db_accruals = []
    for accrual_data in accruals_data:
        db_accrual = Accrual(
            financial_subject_id=accrual_data.financial_subject_id,
            contribution_type_id=accrual_data.contribution_type_id,
            amount=accrual_data.amount,
            accrual_date=accrual_data.accrual_date,
            period_start=accrual_data.period_start,
            period_end=accrual_data.period_end,
            status="created",
        )
        db.add(db_accrual)
        db_accruals.append(db_accrual)

    await db.commit()

    # Refresh все начисления
    for accrual in db_accruals:
        await db.refresh(accrual)

    return db_accruals
