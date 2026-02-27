from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.app_user import AppUser
from app.schemas.payment import PaymentCreate, PaymentInDB
from app.services import payment_service

router = APIRouter()


@router.get(
    "/",
    response_model=list[PaymentInDB],
    summary="Список платежей",
    description="Получить список платежей по финансовому субъекту, владельцу или СТ.",
)
async def get_payments(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    financial_subject_id: UUID | None = Query(None, description="Фильтр по финансовому субъекту"),
    owner_id: UUID | None = Query(None, description="Фильтр по владельцу"),
    cooperative_id: UUID | None = Query(None, description="Фильтр по СТ"),
) -> list[PaymentInDB]:
    """
    Получить список платежей.

    - **admin**: может фильтровать по любому параметру
    - **chairman/treasurer**: видят только платежи своего СТ
    """
    # Для не-admin пользователей используем их СТ
    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id

    if financial_subject_id:
        payments = await payment_service.get_payments_by_financial_subject(db, financial_subject_id)
    elif owner_id:
        payments = await payment_service.get_payments_by_owner(db, owner_id)
    elif cooperative_id:
        payments = await payment_service.get_payments_by_cooperative(db, cooperative_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать financial_subject_id, owner_id или cooperative_id",
        )

    return payments


@router.post(
    "/",
    response_model=PaymentInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Зарегистрировать платёж",
    description="Зарегистрировать новый платёж от владельца. Доступно: treasurer, admin.",
)
async def create_payment(
    payment_data: PaymentCreate,
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    db: AsyncSession = Depends(get_db),
) -> PaymentInDB:
    """Зарегистрировать платёж (treasurer, admin)."""
    # Проверка доступа к финансовому субъекту
    from app.services.balance_service import get_financial_subject

    subject = await get_financial_subject(db, payment_data.financial_subject_id)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Финансовый субъект не найден",
        )

    # Проверка доступа: admin видит все, остальные только своё СТ
    if current_user.role != "admin" and current_user.cooperative_id != subject.cooperative_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к данному финансовому субъекту",
        )

    payment = await payment_service.register_payment(db, payment_data)
    return payment


@router.post(
    "/{payment_id}/cancel",
    response_model=PaymentInDB,
    summary="Отменить платёж",
    description="Изменить статус платежа на 'cancelled'. Доступно: treasurer, admin.",
)
async def cancel_payment(
    payment_id: UUID,
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    db: AsyncSession = Depends(get_db),
) -> PaymentInDB:
    """Отменить платёж (смена статуса на "cancelled") (treasurer, admin)."""
    payment = await payment_service.cancel_payment(db, payment_id)
    return payment
