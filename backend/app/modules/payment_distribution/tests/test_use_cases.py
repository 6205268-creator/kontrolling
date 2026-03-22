"""Tests for payment_distribution use cases."""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.payment_distribution.application.use_cases import (
    CreditAccountUseCase,
    DistributePaymentUseCase,
)
from app.modules.payment_distribution.infrastructure.debt_provider import DebtProvider
from app.modules.payment_distribution.infrastructure.repositories import (
    MemberRepository,
    PaymentDistributionRepository,
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


@pytest.mark.asyncio
async def test_distribute_payment_full_payment_of_single_debt(
    test_db, personal_account_fixture, money_factory
):
    """Test payment fully covers single debt."""
    # Arrange: Create debt (accrual) for member's financial subject
    from app.modules.accruals.infrastructure.models import AccrualModel, ContributionTypeModel
    from app.modules.financial_core.infrastructure.models import FinancialSubjectModel
    from app.modules.land_management.infrastructure.models import LandPlotModel, PlotOwnershipModel

    member = await MemberRepository(test_db).get_by_id(
        personal_account_fixture.member_id, personal_account_fixture.cooperative_id
    )

    # Create land plot and ownership
    plot = LandPlotModel(
        cooperative_id=member.cooperative_id,
        plot_number="1",
        area_sqm=Decimal("600.00"),
    )
    test_db.add(plot)
    await test_db.flush()

    ownership = PlotOwnershipModel(
        land_plot_id=plot.id,
        owner_id=member.owner_id,
        is_primary=True,
        share_numerator=1,
        share_denominator=1,
        valid_from=date.today(),
    )
    test_db.add(ownership)
    await test_db.flush()

    # Create financial subject
    fs = FinancialSubjectModel(
        subject_type="LAND_PLOT",
        subject_id=plot.id,
        cooperative_id=member.cooperative_id,
        code="FS-TEST-1",
    )
    test_db.add(fs)
    await test_db.flush()

    # Create contribution type and accrual (debt)
    ct = ContributionTypeModel(name="Членский взнос", code="MEMBER", description="Тест")
    test_db.add(ct)
    await test_db.flush()

    accrual = AccrualModel(
        financial_subject_id=fs.id,
        contribution_type_id=ct.id,
        amount=Decimal("100.00"),
        accrual_date=date(2025, 1, 1),
        period_start=date(2025, 1, 1),
        period_end=date(2025, 1, 31),
        due_date=date(2025, 1, 31),
        status="applied",
        operation_number="ACC-TEST-1",
    )
    test_db.add(accrual)
    await test_db.commit()

    # Credit account with exact amount
    account_repo = PersonalAccountRepository(test_db)
    account = await account_repo.get_by_member(member.id)
    account.credit(money_factory(100.00))
    await account_repo.update(account)

    # Act: Distribute payment
    distribution_repo = PaymentDistributionRepository(test_db)
    transaction_repo = PersonalAccountTransactionRepository(test_db)
    debt_provider = DebtProvider(test_db)

    use_case = DistributePaymentUseCase(
        member_repo=MemberRepository(test_db),
        account_repo=account_repo,
        distribution_repo=distribution_repo,
        transaction_repo=transaction_repo,
        debt_provider=debt_provider,
    )

    payment_id = uuid4()
    distributions = await use_case.execute(
        payment_id=payment_id,
        owner_id=member.owner_id,
        cooperative_id=member.cooperative_id,
        payment_amount=money_factory(100.00),
    )

    # Assert
    assert len(distributions) == 1
    assert distributions[0].amount.amount == Decimal("100.00")
    assert distributions[0].accrual_id == accrual.id
    assert distributions[0].status == "applied"

    # Check account balance is zero
    account = await account_repo.get_by_member(member.id)
    assert account.balance.amount == Decimal("0.00")

    # Check debit transaction created
    transactions = await transaction_repo.get_by_account(account.id)
    debit_txs = [t for t in transactions if t.type == "debit"]
    assert len(debit_txs) == 1
    assert debit_txs[0].amount.amount == Decimal("100.00")


@pytest.mark.asyncio
async def test_distribute_payment_partial_payment(test_db, personal_account_fixture, money_factory):
    """Test partial payment - payment less than debt."""
    # Arrange: Create debt of 100 BYN
    from app.modules.accruals.infrastructure.models import AccrualModel, ContributionTypeModel
    from app.modules.financial_core.infrastructure.models import FinancialSubjectModel
    from app.modules.land_management.infrastructure.models import LandPlotModel, PlotOwnershipModel

    member = await MemberRepository(test_db).get_by_id(
        personal_account_fixture.member_id, personal_account_fixture.cooperative_id
    )

    plot = LandPlotModel(cooperative_id=member.cooperative_id, plot_number="2", area_sqm=Decimal("600"))
    test_db.add(plot)
    await test_db.flush()

    ownership = PlotOwnershipModel(
        land_plot_id=plot.id, owner_id=member.owner_id, is_primary=True, share_numerator=1, share_denominator=1, valid_from=date.today()
    )
    test_db.add(ownership)
    await test_db.flush()

    fs = FinancialSubjectModel(subject_type="LAND_PLOT", subject_id=plot.id, cooperative_id=member.cooperative_id, code="FS-TEST-2")
    test_db.add(fs)
    await test_db.flush()

    ct = ContributionTypeModel(name="Членский взнос", code="MEMBER", description="Тест")
    test_db.add(ct)
    await test_db.flush()

    accrual = AccrualModel(
        financial_subject_id=fs.id,
        contribution_type_id=ct.id,
        amount=Decimal("100.00"),
        accrual_date=date(2025, 1, 1),
        period_start=date(2025, 1, 1),
        period_end=date(2025, 1, 31),
        due_date=date(2025, 1, 31),
        status="applied",
        operation_number="ACC-TEST-2",
    )
    test_db.add(accrual)
    await test_db.commit()

    # Credit account with partial amount (50 BYN)
    account_repo = PersonalAccountRepository(test_db)
    account = await account_repo.get_by_member(member.id)
    account.credit(money_factory(50.00))
    await account_repo.update(account)

    # Act
    distribution_repo = PaymentDistributionRepository(test_db)
    transaction_repo = PersonalAccountTransactionRepository(test_db)
    debt_provider = DebtProvider(test_db)

    use_case = DistributePaymentUseCase(
        member_repo=MemberRepository(test_db),
        account_repo=account_repo,
        distribution_repo=distribution_repo,
        transaction_repo=transaction_repo,
        debt_provider=debt_provider,
    )

    distributions = await use_case.execute(
        payment_id=uuid4(),
        owner_id=member.owner_id,
        cooperative_id=member.cooperative_id,
        payment_amount=money_factory(50.00),
    )

    # Assert: Partial distribution
    assert len(distributions) == 1
    assert distributions[0].amount.amount == Decimal("50.00")

    # Account balance should be zero (all used)
    account = await account_repo.get_by_member(member.id)
    assert account.balance.amount == Decimal("0.00")


@pytest.mark.asyncio
async def test_distribute_payment_overpayment(test_db, personal_account_fixture, money_factory):
    """Test overpayment - payment more than debt, remainder stays on account."""
    # Arrange: Create debt of 100 BYN
    from app.modules.accruals.infrastructure.models import AccrualModel, ContributionTypeModel
    from app.modules.financial_core.infrastructure.models import FinancialSubjectModel
    from app.modules.land_management.infrastructure.models import LandPlotModel, PlotOwnershipModel

    member = await MemberRepository(test_db).get_by_id(
        personal_account_fixture.member_id, personal_account_fixture.cooperative_id
    )

    plot = LandPlotModel(cooperative_id=member.cooperative_id, plot_number="3", area_sqm=Decimal("600"))
    test_db.add(plot)
    await test_db.flush()

    ownership = PlotOwnershipModel(
        land_plot_id=plot.id, owner_id=member.owner_id, is_primary=True, share_numerator=1, share_denominator=1, valid_from=date.today()
    )
    test_db.add(ownership)
    await test_db.flush()

    fs = FinancialSubjectModel(subject_type="LAND_PLOT", subject_id=plot.id, cooperative_id=member.cooperative_id, code="FS-TEST-3")
    test_db.add(fs)
    await test_db.flush()

    ct = ContributionTypeModel(name="Членский взнос", code="MEMBER", description="Тест")
    test_db.add(ct)
    await test_db.flush()

    accrual = AccrualModel(
        financial_subject_id=fs.id,
        contribution_type_id=ct.id,
        amount=Decimal("100.00"),
        accrual_date=date(2025, 1, 1),
        period_start=date(2025, 1, 1),
        period_end=date(2025, 1, 31),
        due_date=date(2025, 1, 31),
        status="applied",
        operation_number="ACC-TEST-3",
    )
    test_db.add(accrual)
    await test_db.commit()

    # Credit account with overpayment (150 BYN)
    account_repo = PersonalAccountRepository(test_db)
    account = await account_repo.get_by_member(member.id)
    account.credit(money_factory(150.00))
    await account_repo.update(account)

    # Act
    distribution_repo = PaymentDistributionRepository(test_db)
    transaction_repo = PersonalAccountTransactionRepository(test_db)
    debt_provider = DebtProvider(test_db)

    use_case = DistributePaymentUseCase(
        member_repo=MemberRepository(test_db),
        account_repo=account_repo,
        distribution_repo=distribution_repo,
        transaction_repo=transaction_repo,
        debt_provider=debt_provider,
    )

    distributions = await use_case.execute(
        payment_id=uuid4(),
        owner_id=member.owner_id,
        cooperative_id=member.cooperative_id,
        payment_amount=money_factory(150.00),
    )

    # Assert: Only 100 distributed, 50 remains on account
    assert len(distributions) == 1
    assert distributions[0].amount.amount == Decimal("100.00")

    account = await account_repo.get_by_member(member.id)
    assert account.balance.amount == Decimal("50.00")


@pytest.mark.asyncio
async def test_distribute_payment_multiple_debts_priority(test_db, personal_account_fixture, money_factory):
    """Test payment distributed across multiple debts by priority (oldest first)."""
    # Arrange: Create 3 debts (100 each, different due dates)
    from app.modules.accruals.infrastructure.models import AccrualModel, ContributionTypeModel
    from app.modules.financial_core.infrastructure.models import FinancialSubjectModel
    from app.modules.land_management.infrastructure.models import LandPlotModel, PlotOwnershipModel

    member = await MemberRepository(test_db).get_by_id(
        personal_account_fixture.member_id, personal_account_fixture.cooperative_id
    )

    plot = LandPlotModel(cooperative_id=member.cooperative_id, plot_number="4", area_sqm=Decimal("600"))
    test_db.add(plot)
    await test_db.flush()

    ownership = PlotOwnershipModel(
        land_plot_id=plot.id, owner_id=member.owner_id, is_primary=True, share_numerator=1, share_denominator=1, valid_from=date.today()
    )
    test_db.add(ownership)
    await test_db.flush()

    fs = FinancialSubjectModel(subject_type="LAND_PLOT", subject_id=plot.id, cooperative_id=member.cooperative_id, code="FS-TEST-4")
    test_db.add(fs)
    await test_db.flush()

    ct = ContributionTypeModel(name="Членский взнос", code="MEMBER", description="Тест")
    test_db.add(ct)
    await test_db.flush()

    # Create 3 accruals with different due dates
    accruals = []
    for i, due_date_val in enumerate([date(2025, 1, 31), date(2025, 2, 28), date(2025, 3, 31)]):
        accrual = AccrualModel(
            financial_subject_id=fs.id,
            contribution_type_id=ct.id,
            amount=Decimal("100.00"),
            accrual_date=due_date_val.replace(day=1),
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            due_date=due_date_val,
            status="applied",
            operation_number=f"ACC-TEST-{i+4}",
        )
        test_db.add(accrual)
        accruals.append(accrual)
    await test_db.commit()

    # Credit account with 250 BYN (should cover 2.5 debts)
    account_repo = PersonalAccountRepository(test_db)
    account = await account_repo.get_by_member(member.id)
    account.credit(money_factory(250.00))
    await account_repo.update(account)

    # Act
    distribution_repo = PaymentDistributionRepository(test_db)
    transaction_repo = PersonalAccountTransactionRepository(test_db)
    debt_provider = DebtProvider(test_db)

    use_case = DistributePaymentUseCase(
        member_repo=MemberRepository(test_db),
        account_repo=account_repo,
        distribution_repo=distribution_repo,
        transaction_repo=transaction_repo,
        debt_provider=debt_provider,
    )

    distributions = await use_case.execute(
        payment_id=uuid4(),
        owner_id=member.owner_id,
        cooperative_id=member.cooperative_id,
        payment_amount=money_factory(250.00),
    )

    # Assert: Distributed to 2 oldest debts fully, 3rd partially
    assert len(distributions) == 3
    assert distributions[0].amount.amount == Decimal("100.00")  # Oldest
    assert distributions[1].amount.amount == Decimal("100.00")  # Second oldest
    assert distributions[2].amount.amount == Decimal("50.00")   # Third (partial)

    # Priority should be in order
    assert distributions[0].priority == 1
    assert distributions[1].priority == 2
    assert distributions[2].priority == 3

    # Account balance should be zero
    account = await account_repo.get_by_member(member.id)
    assert account.balance.amount == Decimal("0.00")


@pytest.mark.asyncio
async def test_distribute_payment_no_debts(test_db, personal_account_fixture, money_factory):
    """Test payment credited but not distributed when no debts exist."""
    member = await MemberRepository(test_db).get_by_id(
        personal_account_fixture.member_id, personal_account_fixture.cooperative_id
    )

    # Credit account
    account_repo = PersonalAccountRepository(test_db)
    account = await account_repo.get_by_member(member.id)
    account.credit(money_factory(100.00))
    await account_repo.update(account)

    # Act: Distribute with no debts
    distribution_repo = PaymentDistributionRepository(test_db)
    transaction_repo = PersonalAccountTransactionRepository(test_db)
    debt_provider = DebtProvider(test_db)

    use_case = DistributePaymentUseCase(
        member_repo=MemberRepository(test_db),
        account_repo=account_repo,
        distribution_repo=distribution_repo,
        transaction_repo=transaction_repo,
        debt_provider=debt_provider,
    )

    distributions = await use_case.execute(
        payment_id=uuid4(),
        owner_id=member.owner_id,
        cooperative_id=member.cooperative_id,
        payment_amount=money_factory(100.00),
    )

    # Assert: No distributions, money stays on account
    assert len(distributions) == 0

    account = await account_repo.get_by_member(member.id)
    assert account.balance.amount == Decimal("100.00")


@pytest.mark.asyncio
async def test_distribute_payment_zero_balance(test_db, personal_account_fixture, money_factory):
    """Test distribution with zero payment amount."""
    member = await MemberRepository(test_db).get_by_id(
        personal_account_fixture.member_id, personal_account_fixture.cooperative_id
    )

    # Account has zero balance
    account_repo = PersonalAccountRepository(test_db)

    # Act
    distribution_repo = PaymentDistributionRepository(test_db)
    transaction_repo = PersonalAccountTransactionRepository(test_db)
    debt_provider = DebtProvider(test_db)

    use_case = DistributePaymentUseCase(
        member_repo=MemberRepository(test_db),
        account_repo=account_repo,
        distribution_repo=distribution_repo,
        transaction_repo=transaction_repo,
        debt_provider=debt_provider,
    )

    distributions = await use_case.execute(
        payment_id=uuid4(),
        owner_id=member.owner_id,
        cooperative_id=member.cooperative_id,
        payment_amount=money_factory(0.00),
    )

    # Assert: No distributions
    assert len(distributions) == 0
