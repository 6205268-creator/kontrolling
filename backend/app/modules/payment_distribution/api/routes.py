"""Payment Distribution API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.modules.administration.domain.entities import AppUser

from ..application.dtos import (
    PaymentDistributionInDB,
    PaymentDistributionResult,
    PersonalAccountBalance,
    PersonalAccountTransactionInDB,
)
from ..application.use_cases import (
    CreditAccountUseCase,
    DistributePaymentUseCase,
)
from ..infrastructure.repositories import (
    MemberRepository,
    PaymentDistributionRepository,
    PersonalAccountRepository,
    PersonalAccountTransactionRepository,
)

router = APIRouter()


# Dependency injection helpers
def get_member_repository(db=Depends(lambda: None)):  # TODO: Proper DB dependency
    return MemberRepository(db)


def get_account_repository(db=Depends(lambda: None)):
    return PersonalAccountRepository(db)


def get_transaction_repository(db=Depends(lambda: None)):
    return PersonalAccountTransactionRepository(db)


def get_distribution_repository(db=Depends(lambda: None)):
    return PaymentDistributionRepository(db)


def get_credit_account_use_case(
    member_repo=Depends(get_member_repository),
    account_repo=Depends(get_account_repository),
    transaction_repo=Depends(get_transaction_repository),
):
    return CreditAccountUseCase(member_repo, account_repo, transaction_repo)


def get_distribute_payment_use_case(
    member_repo=Depends(get_member_repository),
    account_repo=Depends(get_account_repository),
    distribution_repo=Depends(get_distribution_repository),
    transaction_repo=Depends(get_transaction_repository),
):
    return DistributePaymentUseCase(
        member_repo, account_repo, distribution_repo, transaction_repo
    )


@router.get(
    "/members/{member_id}/account",
    response_model=PersonalAccountBalance,
    summary="Состояние лицевого счёта члена",
    description="Получить информацию о лицевом счёте члена СТ.",
)
async def get_member_account(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    member_id: UUID,
    account_repo: PersonalAccountRepository = Depends(get_account_repository),
    cooperative_id: UUID | None = Query(None, description="ID СТ (для admin)"),
) -> PersonalAccountBalance:
    """Get member's personal account balance."""
    # For non-admin users, use their cooperative
    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id
    elif cooperative_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cooperative_id is required for admin users",
        )

    # Get account by member (simplified - in production get member first)
    account = await account_repo.get_by_member(member_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personal account not found",
        )

    # Get last transaction date
    last_transaction_date = None

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
    transaction_repo: PersonalAccountTransactionRepository = Depends(
        get_transaction_repository
    ),
    account_repo: PersonalAccountRepository = Depends(get_account_repository),
    limit: int = Query(50, ge=1, le=100, description="Лимит записей"),
) -> list[PersonalAccountTransactionInDB]:
    """Get member's personal account transaction history."""
    # Get account
    account = await account_repo.get_by_member(member_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personal account not found",
        )

    # Get transactions
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
    distribution_repo: PaymentDistributionRepository = Depends(
        get_distribution_repository
    ),
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
        remaining_balance=0,  # TODO: Calculate from payment amount
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
    cooperative_id: UUID | None = Query(None, description="ID СТ (для admin)"),
) -> PaymentDistributionResult:
    """Manually trigger payment distribution."""
    # For non-admin users, use their cooperative
    if current_user.role != "admin":
        cooperative_id = current_user.cooperative_id
    elif cooperative_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cooperative_id is required for admin users",
        )

    # TODO: Get payment details and owner_id
    # This is a simplified version - in production you need to get payment first
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Manual distribution not yet implemented",
    )
