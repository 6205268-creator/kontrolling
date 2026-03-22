"""Payment Distribution API routes."""

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.modules.administration.domain.entities import AppUser
from app.modules.deps import (
    get_distribute_payment_use_case,
    get_payment_distribution_repository,
    get_payment_repository,
    get_personal_account_repository,
    get_personal_account_transaction_repository,
)
from app.modules.payment_distribution.application.use_cases import DistributePaymentUseCase

from ..application.dtos import (
    PaymentDistributionInDB,
    PaymentDistributionResult,
    PersonalAccountBalance,
    PersonalAccountTransactionInDB,
)

router = APIRouter()


@router.get(
    "/members/{member_id}/account",
    response_model=PersonalAccountBalance,
    summary="Состояние лицевого счёта члена",
    description="Получить информацию о лицевом счёте члена СТ.",
)
async def get_member_account(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    member_id: UUID,
    account_repo=Depends(get_personal_account_repository),
    transaction_repo=Depends(get_personal_account_transaction_repository),
    cooperative_id: UUID | None = Query(None, description="ID СТ (для admin)"),
) -> PersonalAccountBalance:
    """Get member's personal account balance."""
    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id
    elif cooperative_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cooperative_id is required for admin users",
        )

    account = await account_repo.get_by_member(member_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personal account not found",
        )

    transactions = await transaction_repo.get_by_account(account.id)
    last_transaction_date = transactions[0].transaction_date if transactions else None

    return PersonalAccountBalance(
        account_number=account.account_number,
        balance=account.balance.amount,
        status=account.status,
        last_transaction_date=last_transaction_date,
    )


@router.get(
    "/members/{member_id}/account/transactions",
    response_model=list[PersonalAccountTransactionInDB],
    summary="История транзакций лицевого счёта",
    description="Получить историю транзакций по лицевому счёту члена СТ.",
)
async def get_account_transactions(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    member_id: UUID,
    account_repo=Depends(get_personal_account_repository),
    transaction_repo=Depends(get_personal_account_transaction_repository),
    limit: int = Query(50, ge=1, le=100, description="Лимит записей"),
) -> list[PersonalAccountTransactionInDB]:
    """Get member's personal account transaction history."""
    account = await account_repo.get_by_member(member_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personal account not found",
        )

    transactions = await transaction_repo.get_by_account(account.id)
    return [
        PersonalAccountTransactionInDB(
            id=t.id,
            account_id=t.account_id,
            payment_id=t.payment_id,
            distribution_id=t.distribution_id,
            transaction_number=t.transaction_number,
            transaction_date=t.transaction_date,
            amount=t.amount.amount,
            type=t.type,
            description=t.description,
        )
        for t in transactions[:limit]
    ]


@router.get(
    "/payments/{payment_id}/distributions",
    response_model=PaymentDistributionResult,
    summary="Распределение платежа",
    description="Получить информацию о том, как был распределён платёж.",
)
async def get_payment_distributions(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    payment_id: UUID,
    distribution_repo=Depends(get_payment_distribution_repository),
) -> PaymentDistributionResult:
    """Get payment distribution details."""
    distributions = await distribution_repo.get_by_payment(payment_id)

    if not distributions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment distributions not found",
        )

    total_distributed = sum(d.amount.amount for d in distributions)

    return PaymentDistributionResult(
        payment_id=payment_id,
        total_distributed=total_distributed,
        remaining_balance=Decimal("0"),  # TODO: Get from payment
        distributions=[
            PaymentDistributionInDB(
                id=d.id,
                payment_id=d.payment_id,
                financial_subject_id=d.financial_subject_id,
                accrual_id=d.accrual_id,
                distribution_number=d.distribution_number,
                distributed_at=d.distributed_at,
                amount=d.amount.amount,
                priority=d.priority,
                status=d.status,
            )
            for d in distributions
        ],
    )


@router.post(
    "/payments/{payment_id}/distribute",
    response_model=PaymentDistributionResult,
    summary="Распределить платёж",
    description="Запустить распределение платежа по долгам (если автоматическое не сработало).",
)
async def distribute_payment(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    payment_id: UUID,
    use_case: DistributePaymentUseCase = Depends(get_distribute_payment_use_case),
    payment_repo=Depends(get_payment_repository),
    cooperative_id: UUID | None = Query(None, description="ID СТ (для admin)"),
) -> PaymentDistributionResult:
    """Manually trigger payment distribution."""
    from app.modules.shared.kernel.money import Money

    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id
    elif cooperative_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cooperative_id is required for admin users",
        )

    payment = await payment_repo.get_by_id(payment_id, cooperative_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    distributions = await use_case.execute(
        payment_id=payment_id,
        owner_id=payment.payer_owner_id,
        cooperative_id=cooperative_id,
        payment_amount=Money(payment.amount),
    )

    total_distributed = sum(d.amount.amount for d in distributions)

    return PaymentDistributionResult(
        payment_id=payment_id,
        total_distributed=total_distributed,
        remaining_balance=Decimal("0"),
        distributions=[
            PaymentDistributionInDB(
                id=d.id,
                payment_id=d.payment_id,
                financial_subject_id=d.financial_subject_id,
                accrual_id=d.accrual_id,
                distribution_number=d.distribution_number,
                distributed_at=d.distributed_at,
                amount=d.amount.amount,
                priority=d.priority,
                status=d.status,
            )
            for d in distributions
        ],
    )
