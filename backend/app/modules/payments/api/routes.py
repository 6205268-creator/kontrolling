"""FastAPI routes for payments module."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, require_role
from app.modules.administration.domain.entities import AppUser
from app.modules.deps import (
    get_cancel_payment_use_case,
    get_payments_by_cooperative_use_case,
    get_payments_by_financial_subject_use_case,
    get_payments_by_owner_use_case,
    get_register_payment_use_case,
)
from app.modules.shared.kernel.exceptions import DomainError, ValidationError

from .schemas import PaymentCreate, PaymentInDB

router = APIRouter()


class CancelBody(BaseModel):
    """Request body for cancel endpoint."""
    reason: str | None = Field(None, description="Причина отмены", max_length=512)


@router.get(
    "/",
    response_model=list[PaymentInDB],
    summary="Список платежей",
    description="Получить список платежей по финансовому субъекту, владельцу или СТ.",
)
async def get_payments(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    fs_use_case=Depends(get_payments_by_financial_subject_use_case),
    owner_use_case=Depends(get_payments_by_owner_use_case),
    coop_use_case=Depends(get_payments_by_cooperative_use_case),
    financial_subject_id: UUID | None = Query(None, description="Фильтр по финансовому субъекту"),
    owner_id: UUID | None = Query(None, description="Фильтр по владельцу"),
    cooperative_id: UUID | None = Query(None, description="Фильтр по СТ"),
) -> list[PaymentInDB]:
    """Get list of payments."""
    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id

    payments = []

    if financial_subject_id:
        payments = await fs_use_case.execute(
            financial_subject_id=financial_subject_id,
            cooperative_id=cooperative_id,  # type: ignore[arg-type]
        )
    elif owner_id:
        payments = await owner_use_case.execute(owner_id=owner_id, cooperative_id=cooperative_id)  # type: ignore[arg-type]
    elif cooperative_id:
        payments = await coop_use_case.execute(cooperative_id=cooperative_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать financial_subject_id, owner_id или cooperative_id",
        )

    return [
        PaymentInDB(
            id=p.id,
            financial_subject_id=p.financial_subject_id,
            payer_owner_id=p.payer_owner_id,
            amount=p.amount,
            payment_date=p.payment_date,
            document_number=p.document_number,
            description=p.description,
            status=p.status,
            created_at=p.created_at,
            updated_at=p.updated_at,
            cancelled_at=p.cancelled_at,
            cancelled_by_user_id=p.cancelled_by_user_id,
            cancellation_reason=p.cancellation_reason,
            operation_number=p.operation_number,
        )
        for p in payments
    ]


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
    use_case=Depends(get_register_payment_use_case),
    cooperative_id: UUID | None = Query(None, description="ID СТ (для admin)"),
) -> PaymentInDB:
    """Register a payment."""
    # Для admin используем cooperative_id из query или выбрасываем ошибку
    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id
    elif cooperative_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cooperative_id is required for admin users",
        )
    
    try:
        payment = await use_case.execute(data=payment_data, cooperative_id=cooperative_id)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    return PaymentInDB(
        id=payment.id,
        financial_subject_id=payment.financial_subject_id,
        payer_owner_id=payment.payer_owner_id,
        amount=payment.amount,
        payment_date=payment.payment_date,
        document_number=payment.document_number,
        description=payment.description,
        status=payment.status,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
        cancelled_at=payment.cancelled_at,
        cancelled_by_user_id=payment.cancelled_by_user_id,
        cancellation_reason=payment.cancellation_reason,
        operation_number=payment.operation_number,
    )


@router.post(
    "/{payment_id}/cancel",
    response_model=PaymentInDB,
    summary="Отменить платёж",
    description="Изменить статус платежа на 'cancelled'. Доступно: treasurer, admin.",
)
async def cancel_payment(
    payment_id: UUID,
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    use_case=Depends(get_cancel_payment_use_case),
    cooperative_id: UUID | None = Query(None, description="ID СТ (для admin)"),
    body: CancelBody | None = None,
) -> PaymentInDB:
    """Cancel a payment."""
    # Для admin используем cooperative_id из query или выбрасываем ошибку
    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id
    elif cooperative_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cooperative_id is required for admin users",
        )

    try:
        payment = await use_case.execute(
            payment_id=payment_id,
            cooperative_id=cooperative_id,
            cancelled_by_user_id=current_user.id,
            cancellation_reason=body.reason if body else None,
        )
    except DomainError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return PaymentInDB(
        id=payment.id,
        financial_subject_id=payment.financial_subject_id,
        payer_owner_id=payment.payer_owner_id,
        amount=payment.amount,
        payment_date=payment.payment_date,
        document_number=payment.document_number,
        description=payment.description,
        status=payment.status,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
        cancelled_at=payment.cancelled_at,
        cancelled_by_user_id=payment.cancelled_by_user_id,
        cancellation_reason=payment.cancellation_reason,
        operation_number=payment.operation_number,
    )
