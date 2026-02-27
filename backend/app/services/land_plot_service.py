from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financial_subject import FinancialSubject
from app.models.land_plot import LandPlot
from app.models.plot_ownership import PlotOwnership
from app.schemas.land_plot import LandPlotCreate, LandPlotUpdate
from app.schemas.plot_ownership import PlotOwnershipCreate


async def create_land_plot(
    db: AsyncSession,
    plot: LandPlotCreate,
    ownerships: list[PlotOwnershipCreate] | None = None,
) -> LandPlot:
    """
    Создание земельного участка.

    При создании автоматически создаётся FinancialSubject (subject_type="LAND_PLOT").
    Если переданы ownerships — создаются права собственности.
    """
    # Создаём участок
    db_plot = LandPlot(
        cooperative_id=plot.cooperative_id,
        plot_number=plot.plot_number,
        area_sqm=plot.area_sqm,
        cadastral_number=plot.cadastral_number,
        status=plot.status,
    )
    db.add(db_plot)
    await db.flush()  # Получаем ID участка

    # Создаём финансовый субъект
    financial_subject = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=db_plot.id,
        cooperative_id=plot.cooperative_id,
    )
    db.add(financial_subject)

    # Создаём права собственности если переданы
    if ownerships:
        for ownership in ownerships:
            db_ownership = PlotOwnership(
                land_plot_id=db_plot.id,
                owner_id=ownership.owner_id,
                share_numerator=ownership.share_numerator,
                share_denominator=ownership.share_denominator,
                is_primary=ownership.is_primary,
                valid_from=ownership.valid_from,
                valid_to=ownership.valid_to,
            )
            db.add(db_ownership)

    await db.commit()
    await db.refresh(db_plot)
    return db_plot


async def get_land_plot(db: AsyncSession, plot_id: UUID) -> LandPlot | None:
    """Получение LandPlot по ID."""
    result = await db.execute(select(LandPlot).where(LandPlot.id == plot_id))
    return result.scalar_one_or_none()


async def get_land_plots_by_cooperative(
    db: AsyncSession,
    cooperative_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> list[LandPlot]:
    """Получение списка участков по СТ."""
    query = select(LandPlot).where(LandPlot.cooperative_id == cooperative_id)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_land_plot_with_owners(
    db: AsyncSession,
    plot_id: UUID,
) -> dict | None:
    """
    Получение участка с владельцами и финансовым субъектом.

    Возвращает dict с полями:
    - plot: LandPlot
    - owners: list[PlotOwnership]
    - financial_subject: FinancialSubject | None
    """
    plot = await get_land_plot(db, plot_id)
    if plot is None:
        return None

    # Получаем владельцев
    owners_result = await db.execute(
        select(PlotOwnership)
        .where(PlotOwnership.land_plot_id == plot_id)
        .where(PlotOwnership.valid_to.is_(None))  # Только текущие владельцы
    )
    owners = list(owners_result.scalars().all())

    # Получаем финансовый субъект
    fs_result = await db.execute(
        select(FinancialSubject).where(
            FinancialSubject.subject_type == "LAND_PLOT",
            FinancialSubject.subject_id == plot_id,
        )
    )
    financial_subject = fs_result.scalar_one_or_none()

    return {
        "plot": plot,
        "owners": owners,
        "financial_subject": financial_subject,
    }


async def update_land_plot(
    db: AsyncSession,
    plot_id: UUID,
    data: LandPlotUpdate,
) -> LandPlot | None:
    """Обновление LandPlot."""
    plot = await get_land_plot(db, plot_id)
    if plot is None:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plot, field, value)

    await db.commit()
    await db.refresh(plot)
    return plot


async def delete_land_plot(db: AsyncSession, plot_id: UUID) -> bool:
    """Удаление LandPlot. Возвращает True если удалено."""
    plot = await get_land_plot(db, plot_id)
    if plot is None:
        return False

    await db.delete(plot)
    await db.commit()
    return True


async def add_plot_ownership(
    db: AsyncSession,
    ownership: PlotOwnershipCreate,
) -> PlotOwnership:
    """Добавление владельца к участку."""
    db_ownership = PlotOwnership(
        land_plot_id=ownership.land_plot_id,
        owner_id=ownership.owner_id,
        share_numerator=ownership.share_numerator,
        share_denominator=ownership.share_denominator,
        is_primary=ownership.is_primary,
        valid_from=ownership.valid_from,
        valid_to=ownership.valid_to,
    )
    db.add(db_ownership)
    await db.commit()
    await db.refresh(db_ownership)
    return db_ownership


async def close_plot_ownership(
    db: AsyncSession,
    ownership_id: UUID,
    valid_to: date,
) -> PlotOwnership | None:
    """
    Закрытие права собственности (установка valid_to).

    Возвращает обновлённый PlotOwnership или None если не найден.
    """
    result = await db.execute(
        select(PlotOwnership).where(PlotOwnership.id == ownership_id)
    )
    ownership = result.scalar_one_or_none()
    if ownership is None:
        return None

    ownership.valid_to = valid_to
    await db.commit()
    await db.refresh(ownership)
    return ownership


async def get_plot_ownership(db: AsyncSession, ownership_id: UUID) -> PlotOwnership | None:
    """Получение PlotOwnership по ID."""
    result = await db.execute(
        select(PlotOwnership).where(PlotOwnership.id == ownership_id)
    )
    return result.scalar_one_or_none()
