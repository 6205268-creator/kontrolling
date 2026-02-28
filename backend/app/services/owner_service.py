from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.owner import Owner
from app.schemas.owner import OwnerCreate, OwnerUpdate


async def create_owner(db: AsyncSession, owner: OwnerCreate) -> Owner:
    """Создание нового Owner."""
    db_owner = Owner(
        owner_type=owner.owner_type,
        name=owner.name,
        tax_id=owner.tax_id,
        contact_phone=owner.contact_phone,
        contact_email=owner.contact_email,
    )
    db.add(db_owner)
    await db.commit()
    await db.refresh(db_owner)
    return db_owner


async def get_owner(db: AsyncSession, owner_id: UUID) -> Owner | None:
    """Получение Owner по ID."""
    result = await db.execute(select(Owner).where(Owner.id == owner_id))
    return result.scalar_one_or_none()


async def get_owners(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> list[Owner]:
    """Получение списка Owner."""
    query = select(Owner).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_owner(
    db: AsyncSession,
    owner_id: UUID,
    data: OwnerUpdate,
) -> Owner | None:
    """Обновление Owner."""
    owner = await get_owner(db, owner_id)
    if owner is None:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(owner, field, value)

    await db.commit()
    await db.refresh(owner)
    return owner


async def delete_owner(db: AsyncSession, owner_id: UUID) -> bool:
    """Удаление Owner. Возвращает True если удалено."""
    owner = await get_owner(db, owner_id)
    if owner is None:
        return False

    await db.delete(owner)
    await db.commit()
    return True


async def search_owners(
    db: AsyncSession,
    query: str,
    limit: int = 100,
) -> list[Owner]:
    """
    Поиск владельцев по имени или tax_id.

    Ищет частичное совпадение в name или tax_id.
    """
    search_pattern = f"%{query}%"
    stmt = (
        select(Owner)
        .where((Owner.name.ilike(search_pattern)) | (Owner.tax_id.ilike(search_pattern)))
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
