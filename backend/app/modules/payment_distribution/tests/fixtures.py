"""Fixtures for payment_distribution tests."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.modules.shared.kernel.money import Money


@pytest.fixture
async def member_fixture(test_db):
    """Create a test member."""
    from app.modules.cooperative_core.infrastructure.models import CooperativeModel
    from app.modules.land_management.infrastructure.models import OwnerModel
    from app.modules.payment_distribution.infrastructure.models import MemberModel

    # Create cooperative and owner
    coop = CooperativeModel(name="СТ Тест", unp="123456789")
    test_db.add(coop)
    await test_db.flush()

    owner = OwnerModel(owner_type="physical", name="Тестовый Владелец")
    test_db.add(owner)
    await test_db.flush()

    # Create member
    member = MemberModel(
        owner_id=owner.id,
        cooperative_id=coop.id,
        status="active",
        joined_at=datetime.now(UTC),
    )
    test_db.add(member)
    await test_db.commit()

    return member


@pytest.fixture
async def personal_account_fixture(test_db, member_fixture):
    """Create a test personal account for member."""
    from app.modules.payment_distribution.infrastructure.models import PersonalAccountModel

    account = PersonalAccountModel(
        member_id=member_fixture.id,
        cooperative_id=member_fixture.cooperative_id,
        account_number=f"PA-{member_fixture.cooperative_id.hex[:8]}-{member_fixture.id.hex[:8]}",
        balance=Decimal("0.00"),
        status="active",
        opened_at=datetime.now(UTC),
    )
    test_db.add(account)
    await test_db.commit()

    # Update member with personal_account_id
    member_fixture.personal_account_id = account.id
    await test_db.commit()

    return account


@pytest.fixture
def money_factory():
    """Factory for creating Money objects."""

    def _create(amount: float | Decimal) -> Money:
        return Money(Decimal(str(amount)))

    return _create
