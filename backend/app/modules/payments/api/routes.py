"""FastAPI routes for payments module."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.app_user import AppUser

from .schemas import PaymentCreate, PaymentInDB
from ..infrastructure.repositories import PaymentRepository
from ..application.use_cases import (
    RegisterPaymentUseCase,
    GetPaymentUseCase,
    GetPaymentsByFinancialSubjectUseCase,
    GetPaymentsByOwnerUseCase,
    GetPaymentsByCooperativeUseCase,
    CancelPaymentUseCase,
)

router = APIRouter()


def _get_payment_repo(db: AsyncSession) -> PaymentRepository:
    """Get payment repository instance."""
    return PaymentRepository(db)


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
    """Get list of payments."""
    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id

    repo = _get_payment_repo(db)
    payments = []
    
    if financial_subject_id:
        use_case = GetPaymentsByFinancialSubjectUseCase(repo)
        payments = await use_case.execute(
            financial_subject_id=financial_subject_id,
            cooperative_id=cooperative_id,  # type: ignore[arg-type]
        )
    elif owner_id:
        use_case = GetPaymentsByOwnerUseCase(repo)
        payments = await use_case.execute(owner_id=owner_id, cooperative_id=cooperative_id)  # type: ignore[arg-type]
    elif cooperative_id:
        use_case = GetPaymentsByCooperativeUseCase(repo)
        payments = await use_case.execute(cooperative_id=cooperative_id)
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
    db: AsyncSession = Depends(get_db),
) -> PaymentInDB:
    """Register a payment."""
    from app.modules.financial_core.infrastructure.repositories import FinancialSubjectRepository
    
    fs_repo = FinancialSubjectRepository(db)
    subject = await fs_repo.get_by_id(payment_data.financial_subject_id, current_user.cooperative_id)
    
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Финансовый субъект не найден",
        )

    if current_user.role != "admin" and current_user.cooperative_id != subject.cooperative_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к данному финансовому субъекту",
        )

    repo = _get_payment_repo(db)
    use_case = RegisterPaymentUseCase(repo)
    
    payment = await use_case.execute(data=payment_data, cooperative_id=current_user.cooperative_id)
    
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
    db: AsyncSession = Depends(get_db),
) -> PaymentInDB:
    """Cancel a payment."""
    repo = _get_payment_repo(db)
    use_case = CancelPaymentUseCase(repo)
    
    try:
        payment = await use_case.execute(payment_id=payment_id, cooperative_id=current_user.cooperative_id)
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
    )
