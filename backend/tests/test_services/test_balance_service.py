from datetime import date
from decimal import Decimal

import pytest

from app.models.accrual import Accrual
from app.models.contribution_type import ContributionType
from app.models.financial_subject import FinancialSubject
from app.models.payment import Payment
from app.services.balance_service import calculate_balance, get_balances_by_cooperative


@pytest.mark.asyncio
async def test_calculate_balance_simple(test_db) -> None:
    """Тест расчёта баланса: одно начисление и один платёж."""
    # Создаём СТ
    from app.models.cooperative import Cooperative

    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    # Создаём финансовый субъект
    subject = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=coop.id,  # Временный ID
        cooperative_id=coop.id,
    )
    test_db.add(subject)
    await test_db.flush()

    # Создаём вид взноса
    contribution_type = ContributionType(name="Членский", code="MEMBER")
    test_db.add(contribution_type)
    await test_db.flush()

    # Создаём начисление (applied)
    accrual = Accrual(
        financial_subject_id=subject.id,
        contribution_type_id=contribution_type.id,
        amount=Decimal("1000.00"),
        accrual_date=date.today(),
        period_start=date.today().replace(month=1, day=1),
        status="applied",
    )
    test_db.add(accrual)

    # Создаём владельца для платежа
    from app.models.owner import Owner

    owner = Owner(owner_type="physical", name="Тест")
    test_db.add(owner)
    await test_db.flush()

    # Создаём платёж (confirmed)
    payment = Payment(
        financial_subject_id=subject.id,
        payer_owner_id=owner.id,
        amount=Decimal("600.00"),
        payment_date=date.today(),
        status="confirmed",
    )
    test_db.add(payment)
    await test_db.commit()

    # Проверяем расчёт
    balance = await calculate_balance(test_db, subject.id)

    assert balance is not None
    assert balance.total_accruals == Decimal("1000.00")
    assert balance.total_payments == Decimal("600.00")
    assert balance.balance == Decimal("400.00")


@pytest.mark.asyncio
async def test_calculate_balance_multiple_accruals(test_db) -> None:
    """Тест с несколькими начислениями."""
    from app.models.cooperative import Cooperative
    from app.models.owner import Owner

    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    subject = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=coop.id,
        cooperative_id=coop.id,
    )
    test_db.add(subject)
    await test_db.flush()

    contribution_type = ContributionType(name="Членский", code="MEMBER")
    test_db.add(contribution_type)
    await test_db.flush()

    # Несколько начислений
    for amount in [Decimal("500.00"), Decimal("300.00"), Decimal("200.00")]:
        accrual = Accrual(
            financial_subject_id=subject.id,
            contribution_type_id=contribution_type.id,
            amount=amount,
            accrual_date=date.today(),
            period_start=date.today().replace(month=1, day=1),
            status="applied",
        )
        test_db.add(accrual)

    owner = Owner(owner_type="physical", name="Тест")
    test_db.add(owner)
    await test_db.commit()

    balance = await calculate_balance(test_db, subject.id)

    assert balance is not None
    assert balance.total_accruals == Decimal("1000.00")
    assert balance.total_payments == Decimal("0.00")
    assert balance.balance == Decimal("1000.00")


@pytest.mark.asyncio
async def test_calculate_balance_multiple_payments(test_db) -> None:
    """Тест с несколькими платежами."""
    from app.models.cooperative import Cooperative
    from app.models.owner import Owner

    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    subject = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=coop.id,
        cooperative_id=coop.id,
    )
    test_db.add(subject)
    await test_db.flush()

    contribution_type = ContributionType(name="Членский", code="MEMBER")
    test_db.add(contribution_type)
    await test_db.flush()

    # Начисление
    accrual = Accrual(
        financial_subject_id=subject.id,
        contribution_type_id=contribution_type.id,
        amount=Decimal("1000.00"),
        accrual_date=date.today(),
        period_start=date.today().replace(month=1, day=1),
        status="applied",
    )
    test_db.add(accrual)

    # Несколько платежей
    owner = Owner(owner_type="physical", name="Тест")
    test_db.add(owner)
    await test_db.flush()

    for amount in [Decimal("400.00"), Decimal("300.00"), Decimal("200.00")]:
        payment = Payment(
            financial_subject_id=subject.id,
            payer_owner_id=owner.id,
            amount=amount,
            payment_date=date.today(),
            status="confirmed",
        )
        test_db.add(payment)

    await test_db.commit()

    balance = await calculate_balance(test_db, subject.id)

    assert balance is not None
    assert balance.total_accruals == Decimal("1000.00")
    assert balance.total_payments == Decimal("900.00")
    assert balance.balance == Decimal("100.00")


@pytest.mark.asyncio
async def test_calculate_balance_only_created_accruals(test_db) -> None:
    """Тест: начисления со статусом 'created' не учитываются."""
    from app.models.cooperative import Cooperative
    from app.models.owner import Owner

    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    subject = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=coop.id,
        cooperative_id=coop.id,
    )
    test_db.add(subject)
    await test_db.flush()

    contribution_type = ContributionType(name="Членский", code="MEMBER")
    test_db.add(contribution_type)
    await test_db.flush()

    # Начисление со статусом 'created' (не 'applied')
    accrual = Accrual(
        financial_subject_id=subject.id,
        contribution_type_id=contribution_type.id,
        amount=Decimal("1000.00"),
        accrual_date=date.today(),
        period_start=date.today().replace(month=1, day=1),
        status="created",  # Не applied
    )
    test_db.add(accrual)

    owner = Owner(owner_type="physical", name="Тест")
    test_db.add(owner)
    await test_db.commit()

    balance = await calculate_balance(test_db, subject.id)

    assert balance is not None
    assert balance.total_accruals == Decimal("0.00")  # Не учитывается
    assert balance.total_payments == Decimal("0.00")
    assert balance.balance == Decimal("0.00")


@pytest.mark.asyncio
async def test_calculate_balance_subject_not_found(test_db) -> None:
    """Тест: субъект не найден."""
    import uuid

    fake_id = uuid.uuid4()

    balance = await calculate_balance(test_db, fake_id)

    assert balance is None


@pytest.mark.asyncio
async def test_get_balances_by_cooperative(test_db) -> None:
    """Тест получения балансов всех субъектов СТ."""
    from app.models.cooperative import Cooperative
    from app.models.land_plot import LandPlot
    from app.models.owner import Owner

    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    # Создаём несколько финансовых субъектов с разными subject_id
    subjects = []
    for i in range(3):
        # Создаём разные участки для разных subject_id
        plot = LandPlot(
            cooperative_id=coop.id,
            plot_number=f"Участок {i}",
            area_sqm=Decimal("500.00"),
        )
        test_db.add(plot)
        await test_db.flush()

        subject = FinancialSubject(
            subject_type="LAND_PLOT",
            subject_id=plot.id,
            cooperative_id=coop.id,
            code=f"FS-TEST{i}",
        )
        test_db.add(subject)
        subjects.append(subject)
    await test_db.flush()

    contribution_type = ContributionType(name="Членский", code="MEMBER")
    test_db.add(contribution_type)
    await test_db.flush()

    # Создаём начисления для разных субъектов
    for i, subject in enumerate(subjects):
        accrual = Accrual(
            financial_subject_id=subject.id,
            contribution_type_id=contribution_type.id,
            amount=Decimal(f"{(i + 1) * 100}.00"),
            accrual_date=date.today(),
            period_start=date.today().replace(month=1, day=1),
            status="applied",
        )
        test_db.add(accrual)

    owner = Owner(owner_type="physical", name="Тест")
    test_db.add(owner)
    await test_db.commit()

    balances = await get_balances_by_cooperative(test_db, coop.id)

    assert len(balances) == 3
    assert balances[0].balance == Decimal("100.00")
    assert balances[1].balance == Decimal("200.00")
    assert balances[2].balance == Decimal("300.00")


@pytest.mark.asyncio
async def test_get_balances_by_cooperative_empty(test_db) -> None:
    """Тест: у СТ нет финансовых субъектов."""
    from app.models.cooperative import Cooperative

    coop = Cooperative(name="СТ Пустое")
    test_db.add(coop)
    await test_db.commit()

    balances = await get_balances_by_cooperative(test_db, coop.id)

    assert len(balances) == 0
