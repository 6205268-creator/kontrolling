import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.land_management.infrastructure.models import OwnerModel as Owner


@pytest.mark.asyncio
async def test_create_owner_physical(test_db: AsyncSession) -> None:
    """Создание Owner с типом physical."""
    owner = Owner(
        owner_type="physical",
        name="Иванов Иван Иванович",
        tax_id="12345678901234",
        contact_phone="+375291234567",
    )
    test_db.add(owner)
    await test_db.commit()
    await test_db.refresh(owner)
    assert owner.id is not None
    assert isinstance(owner.id, uuid.UUID)
    assert owner.owner_type == "physical"
    assert owner.name == "Иванов Иван Иванович"
    assert owner.tax_id == "12345678901234"
    assert owner.contact_phone == "+375291234567"
    assert owner.contact_email is None


@pytest.mark.asyncio
async def test_create_owner_legal(test_db: AsyncSession) -> None:
    """Создание Owner с типом legal."""
    owner = Owner(
        owner_type="legal",
        name="Исполком Ленинского района",
        tax_id="123456789",
        contact_email="admin@example.by",
    )
    test_db.add(owner)
    await test_db.commit()
    await test_db.refresh(owner)
    assert owner.owner_type == "legal"
    assert owner.name == "Исполком Ленинского района"
    assert owner.contact_email == "admin@example.by"


@pytest.mark.asyncio
async def test_owner_type_values(test_db: AsyncSession) -> None:
    """Валидация: сохраняются только допустимые owner_type (physical, legal)."""
    for owner_type in ("physical", "legal"):
        owner = Owner(owner_type=owner_type, name=f"Test {owner_type}")
        test_db.add(owner)
    await test_db.commit()
    from sqlalchemy import select

    result = await test_db.execute(select(Owner))
    owners = result.scalars().all()
    assert len(owners) == 2
    types = {o.owner_type for o in owners}
    assert types == {"physical", "legal"}
