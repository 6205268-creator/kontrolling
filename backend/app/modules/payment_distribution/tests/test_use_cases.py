"""Tests for payment_distribution use cases."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.payment_distribution.application.use_cases import CreditAccountUseCase
from app.modules.payment_distribution.infrastructure.repositories import (
    MemberRepository,
    PersonalAccountRepository,
    PersonalAccountTransactionRepository,
)


@pytest.mark.asyncio
async def test_credit_account_creates_account_and_transaction(
    test_db, member_fixture, money_factory
):
    """Test that crediting account creates account if not exists and creates transaction."""
    # Arrange
    member = member_fixture
    payment_id = uuid4()
    amount = money_factory(100.00)
    payment_date = datetime.now(UTC)

    account_repo = PersonalAccountRepository(test_db)
    transaction_repo = PersonalAccountTransactionRepository(test_db)
    member_repo = MemberRepository(test_db)

    use_case = CreditAccountUseCase(
        member_repo=member_repo,
        account_repo=account_repo,
        transaction_repo=transaction_repo,
    )

    # Act
    await use_case.execute(
        payment_id=payment_id,
        owner_id=member.owner_id,
        cooperative_id=member.cooperative_id,
        amount=amount,
        payment_date=payment_date,
    )

    # Assert
    account = await account_repo.get_by_member(member.id)
    assert account is not None
    assert account.balance.amount == Decimal("100.00")

    transactions = await transaction_repo.get_by_account(account.id)
    assert len(transactions) == 1
    assert transactions[0].type == "credit"
    assert transactions[0].amount.amount == Decimal("100.00")
    assert transactions[0].payment_id == payment_id


@pytest.mark.asyncio
async def test_credit_account_updates_existing_balance(
    test_db, personal_account_fixture, money_factory
):
    """Test that crediting account updates existing balance."""
    # Arrange
    member = await MemberRepository(test_db).get_by_id(
        personal_account_fixture.member_id, personal_account_fixture.cooperative_id
    )
    payment_id = uuid4()
    amount = money_factory(150.00)
    payment_date = datetime.now(UTC)

    account_repo = PersonalAccountRepository(test_db)
    transaction_repo = PersonalAccountTransactionRepository(test_db)
    member_repo = MemberRepository(test_db)

    use_case = CreditAccountUseCase(
        member_repo=member_repo,
        account_repo=account_repo,
        transaction_repo=transaction_repo,
    )

    # Act
    await use_case.execute(
        payment_id=payment_id,
        owner_id=member.owner_id,
        cooperative_id=member.cooperative_id,
        amount=amount,
        payment_date=payment_date,
    )

    # Assert
    account = await account_repo.get_by_member(member.id)
    assert account.balance.amount == Decimal("150.00")

    transactions = await transaction_repo.get_by_account(account.id)
    assert len(transactions) == 1
    assert transactions[0].type == "credit"


@pytest.mark.asyncio
async def test_credit_account_multiple_payments(
    test_db, personal_account_fixture, money_factory
):
    """Test multiple payments credit correctly."""
    # Arrange
    member = await MemberRepository(test_db).get_by_id(
        personal_account_fixture.member_id, personal_account_fixture.cooperative_id
    )
    account_repo = PersonalAccountRepository(test_db)
    transaction_repo = PersonalAccountTransactionRepository(test_db)
    member_repo = MemberRepository(test_db)

    use_case = CreditAccountUseCase(
        member_repo=member_repo,
        account_repo=account_repo,
        transaction_repo=transaction_repo,
    )

    # Act - Credit 3 payments
    for i in range(3):
        await use_case.execute(
            payment_id=uuid4(),
            owner_id=member.owner_id,
            cooperative_id=member.cooperative_id,
            amount=money_factory(50.00),
            payment_date=datetime.now(UTC),
        )

    # Assert
    account = await account_repo.get_by_member(member.id)
    assert account.balance.amount == Decimal("150.00")

    transactions = await transaction_repo.get_by_account(account.id)
    assert len(transactions) == 3
    assert all(t.type == "credit" for t in transactions)
