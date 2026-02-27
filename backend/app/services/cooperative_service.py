from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cooperative import Cooperative
from app.schemas.cooperative import CooperativeCreate, CooperativeUpdate


async def create_cooperative(db: AsyncSession, cooperative: CooperativeCreate) -> Cooperative:
    """Создание нового Cooperative."""
    db_cooperative = Cooperative(
        name=cooperative.name,
        unp=cooperative.unp,
        address=cooperative.address,
    )
    db.add(db_cooperative)
    await db.commit()
    await db.refresh(db_cooperative)
    return db_cooperative


async def get_cooperative(db: AsyncSession, cooperative_id: UUID) -> Cooperative | None:
    """Получение Cooperative по ID."""
    result = await db.execute(select(Cooperative).where(Cooperative.id == cooperative_id))
    return result.scalar_one_or_none()


async def get_cooperatives(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    cooperative_id: UUID | None = None,
) -> list[Cooperative]:
    """
    Получение списка Cooperative.

    Если указан cooperative_id, возвращается только одно СТ.
    Для admin можно передать None для получения всех.
    """
    query = select(Cooperative)
    if cooperative_id:
        query = query.where(Cooperative.id == cooperative_id)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_cooperative(
    db: AsyncSession,
    cooperative_id: UUID,
    data: CooperativeUpdate,
) -> Cooperative | None:
    """Обновление Cooperative."""
    cooperative = await get_cooperative(db, cooperative_id)
    if cooperative is None:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cooperative, field, value)

    await db.commit()
    await db.refresh(cooperative)
    return cooperative


async def delete_cooperative(db: AsyncSession, cooperative_id: UUID) -> bool:
    """Удаление Cooperative. Возвращает True если удалено."""
    cooperative = await get_cooperative(db, cooperative_id)
    if cooperative is None:
        return False

    await db.delete(cooperative)
    await db.commit()
    return True
