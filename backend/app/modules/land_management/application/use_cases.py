"""Use cases for land_management module."""

import logging
import uuid
from datetime import date
from uuid import UUID

from app.modules.financial_core.domain.entities import FinancialSubject
from app.modules.financial_core.domain.repositories import IFinancialSubjectRepository
from app.modules.shared.kernel.events import EventDispatcher
from app.modules.shared.kernel.exceptions import ValidationError

from ..domain.entities import LandPlot, Owner, PlotOwnership
from ..domain.events import (
    LandPlotCreated,
    OwnerCreated,
    PlotOwnershipCreated,
    PlotOwnershipTransferred,
)
from ..domain.repositories import ILandPlotRepository, IOwnerRepository, IPlotOwnershipRepository
from .dtos import LandPlotCreate, LandPlotUpdate, OwnerCreate, OwnerUpdate, PlotOwnershipCreate

logger = logging.getLogger(__name__)


class CreateLandPlotUseCase:
    """Use case for creating a new LandPlot.

    Creates both LandPlot and FinancialSubject atomically.
    """

    def __init__(
        self,
        land_plot_repo: ILandPlotRepository,
        ownership_repo: IPlotOwnershipRepository,
        fs_repo: IFinancialSubjectRepository,
        event_dispatcher: EventDispatcher,
    ):
        self.land_plot_repo = land_plot_repo
        self.ownership_repo = ownership_repo
        self.fs_repo = fs_repo
        self.event_dispatcher = event_dispatcher

    async def execute(
        self,
        data: LandPlotCreate,
        ownerships: list[PlotOwnershipCreate] | None = None,
    ) -> LandPlot:
        """Create a new land plot with optional ownerships.

        Args:
            data: DTO with land plot data.
            ownerships: Optional list of ownership records to create.

        Returns:
            Created LandPlot entity.

        Raises:
            ValidationError: If validation fails.
        """
        # Domain validation
        if not data.plot_number or len(data.plot_number) > 50:
            raise ValidationError("Plot number must be between 1 and 50 characters")

        if data.cadastral_number and len(data.cadastral_number) > 50:
            raise ValidationError("Cadastral number must not exceed 50 characters")

        # Create land plot
        entity = LandPlot(
            id=UUID(int=0),  # Will be set by repository
            cooperative_id=data.cooperative_id,
            plot_number=data.plot_number,
            area_sqm=data.area_sqm,
            cadastral_number=data.cadastral_number,
            status=data.status,
        )

        created_plot = await self.land_plot_repo.add(entity)

        # Create FinancialSubject atomically
        fs_code = f"FS-LP-{created_plot.plot_number}"
        fs = FinancialSubject(
            id=UUID(int=0),
            subject_type="LAND_PLOT",
            subject_id=created_plot.id,
            cooperative_id=created_plot.cooperative_id,
            code=fs_code,
            status="active",
        )
        await self.fs_repo.add(fs)

        # Create ownerships if provided
        if ownerships:
            for ownership_data in ownerships:
                ownership = PlotOwnership(
                    id=uuid.uuid4(),
                    land_plot_id=created_plot.id,
                    owner_id=ownership_data.owner_id,
                    share_numerator=ownership_data.share_numerator,
                    share_denominator=ownership_data.share_denominator,
                    is_primary=ownership_data.is_primary,
                    valid_from=ownership_data.valid_from,
                    valid_to=ownership_data.valid_to,
                )
                await self.ownership_repo.add(ownership)

        # Publish domain event for other modules (notifications, analytics, etc.)
        self.event_dispatcher.dispatch(
            LandPlotCreated(
                land_plot_id=created_plot.id,
                cooperative_id=created_plot.cooperative_id,
                plot_number=created_plot.plot_number,
                area_sqm=float(created_plot.area_sqm),
            )
        )

        # Return plot with financial subject info
        return created_plot, fs


class GetLandPlotUseCase:
    """Use case for getting a LandPlot by ID."""

    def __init__(self, repo: ILandPlotRepository):
        self.repo = repo

    async def execute(self, plot_id: UUID, cooperative_id: UUID | None) -> LandPlot | None:
        """Get land plot by ID. If cooperative_id is None (admin), no cooperative filter."""
        if cooperative_id is None:
            return await self.repo.get_by_id_any_cooperative(plot_id)
        return await self.repo.get_by_id(plot_id, cooperative_id)


class GetLandPlotsUseCase:
    """Use case for getting list of LandPlots."""

    def __init__(self, repo: ILandPlotRepository):
        self.repo = repo

    async def execute(
        self, cooperative_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[LandPlot]:
        """Get list of land plots for cooperative."""
        plots = await self.repo.get_all(cooperative_id)
        return plots[skip : skip + limit]


class UpdateLandPlotUseCase:
    """Use case for updating a LandPlot.

    If ownerships is provided, current ownerships are closed (valid_to=today)
    and the given list is created as new ownerships.
    """

    def __init__(
        self,
        repo: ILandPlotRepository,
        get_current_ownerships: "GetCurrentPlotOwnershipsUseCase",
        close_ownership: "ClosePlotOwnershipUseCase",
        create_ownership: "CreatePlotOwnershipUseCase",
    ):
        self.repo = repo
        self.get_current_ownerships = get_current_ownerships
        self.close_ownership = close_ownership
        self.create_ownership = create_ownership

    async def execute(
        self,
        plot_id: UUID,
        data: LandPlotUpdate,
        cooperative_id: UUID | None,
    ) -> LandPlot | None:
        """Update land plot and optionally replace ownerships."""
        logger.info(
            "UpdateLandPlotUseCase.execute: plot_id=%s, cooperative_id=%s, data keys=%s",
            plot_id,
            cooperative_id,
            list(data.model_dump(exclude_unset=True).keys()) if hasattr(data, "model_dump") else [],
        )
        ownerships_raw = getattr(data, "ownerships", None)
        logger.info(
            "UpdateLandPlotUseCase: ownerships from request: present=%s, count=%s",
            ownerships_raw is not None,
            len(ownerships_raw) if ownerships_raw else 0,
        )

        if cooperative_id is None:
            entity = await self.repo.get_by_id_any_cooperative(plot_id)
        else:
            entity = await self.repo.get_by_id(plot_id, cooperative_id)
        if entity is None:
            logger.warning("UpdateLandPlotUseCase: plot not found, plot_id=%s", plot_id)
            return None

        # For ownership operations use plot's cooperative (admin has cooperative_id=None)
        effective_cooperative_id = (
            cooperative_id if cooperative_id is not None else entity.cooperative_id
        )
        logger.info(
            "UpdateLandPlotUseCase: effective_cooperative_id=%s",
            effective_cooperative_id,
        )

        update_data = data.model_dump(exclude_unset=True)
        # ownerships читаем из data: при PATCH могут передать не все поля, в dump может не попасть
        ownerships_payload = getattr(data, "ownerships", None)
        if ownerships_payload is not None:
            ownerships_payload = [
                u.model_dump() if hasattr(u, "model_dump") else dict(u) for u in ownerships_payload
            ]
            logger.info(
                "UpdateLandPlotUseCase: ownerships_payload (serialized) count=%s, items=%s",
                len(ownerships_payload),
                ownerships_payload,
            )
        update_data.pop("ownerships", None)

        for field, value in update_data.items():
            if hasattr(entity, field):
                setattr(entity, field, value)

        updated_plot = await self.repo.update(entity)
        logger.info("UpdateLandPlotUseCase: plot fields updated successfully")

        if ownerships_payload is not None:
            current = await self.get_current_ownerships.execute(plot_id)
            logger.info(
                "UpdateLandPlotUseCase: current ownerships to close: count=%s, ids=%s",
                len(current),
                [str(o.id) for o in current],
            )
            today = date.today()
            for o in current:
                await self.close_ownership.execute(o.id, today, effective_cooperative_id)
                logger.info("UpdateLandPlotUseCase: closed ownership id=%s", o.id)
            for i, ownership_data in enumerate(ownerships_payload):
                try:
                    dto = PlotOwnershipCreate(**ownership_data)
                    await self.create_ownership.execute(
                        land_plot_id=plot_id,
                        data=dto,
                        cooperative_id=effective_cooperative_id,
                    )
                    logger.info(
                        "UpdateLandPlotUseCase: created ownership #%s owner_id=%s",
                        i + 1,
                        ownership_data.get("owner_id"),
                    )
                except Exception as e:
                    logger.exception(
                        "UpdateLandPlotUseCase: failed to create ownership #%s, payload=%s: %s",
                        i + 1,
                        ownership_data,
                        e,
                    )
                    raise

        return updated_plot


class DeleteLandPlotUseCase:
    """Use case for deleting a LandPlot."""

    def __init__(self, repo: ILandPlotRepository):
        self.repo = repo

    async def execute(self, plot_id: UUID, cooperative_id: UUID | None) -> bool:
        """Delete land plot by ID."""
        # For admin (cooperative_id=None), delete without cooperative filter
        if cooperative_id is None:
            # Admin can delete any plot - use repository method that doesn't filter by cooperative
            return await self.repo.delete_by_id_any_cooperative(plot_id)

        entity = await self.repo.get_by_id(plot_id, cooperative_id)
        if entity is None:
            return False

        await self.repo.delete(plot_id, cooperative_id)
        return True


class CreateOwnerUseCase:
    """Use case for creating a new Owner."""

    def __init__(self, repo: IOwnerRepository, event_dispatcher: EventDispatcher):
        self.repo = repo
        self.event_dispatcher = event_dispatcher

    async def execute(self, data: OwnerCreate) -> Owner:
        """Create a new owner."""
        # Domain validation
        if not data.name or len(data.name) > 255:
            raise ValidationError("Name must be between 1 and 255 characters")

        if data.tax_id and len(data.tax_id) > 20:
            raise ValidationError("Tax ID must not exceed 20 characters")

        entity = Owner(
            id=UUID(int=0),
            owner_type=data.owner_type,
            name=data.name,
            tax_id=data.tax_id,
            contact_phone=data.contact_phone,
            contact_email=data.contact_email,
        )

        created_owner = await self.repo.add(entity)

        # Publish domain event
        self.event_dispatcher.dispatch(
            OwnerCreated(
                owner_id=created_owner.id,
                owner_type=created_owner.owner_type,
                name=created_owner.name,
            )
        )

        return created_owner


class GetOwnerUseCase:
    """Use case for getting an Owner by ID."""

    def __init__(self, repo: IOwnerRepository):
        self.repo = repo

    async def execute(self, owner_id: UUID) -> Owner | None:
        """Get owner by ID."""
        return await self.repo.get_by_id(
            owner_id, UUID(int=0)
        )  # cooperative_id not used for owners


class GetOwnersUseCase:
    """Use case for getting list of Owners."""

    def __init__(self, repo: IOwnerRepository):
        self.repo = repo

    async def execute(self, skip: int = 0, limit: int = 100) -> list[Owner]:
        """Get list of owners."""
        owners = await self.repo.get_all(UUID(int=0))  # cooperative_id not used for owners
        return owners[skip : skip + limit]


class UpdateOwnerUseCase:
    """Use case for updating an Owner."""

    def __init__(self, repo: IOwnerRepository):
        self.repo = repo

    async def execute(
        self,
        owner_id: UUID,
        data: OwnerUpdate,
    ) -> Owner | None:
        """Update owner."""
        entity = await self.repo.get_by_id(owner_id, UUID(int=0))
        if entity is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(entity, field):
                setattr(entity, field, value)

        return await self.repo.update(entity)


class DeleteOwnerUseCase:
    """Use case for deleting an Owner."""

    def __init__(self, repo: IOwnerRepository):
        self.repo = repo

    async def execute(self, owner_id: UUID) -> bool:
        """Delete owner by ID."""
        entity = await self.repo.get_by_id(owner_id, UUID(int=0))
        if entity is None:
            return False

        await self.repo.delete(owner_id, UUID(int=0))
        return True


class SearchOwnersUseCase:
    """Use case for searching Owners."""

    def __init__(self, repo: IOwnerRepository):
        self.repo = repo

    async def execute(self, query: str, limit: int = 100) -> list[Owner]:
        """Search owners by name or tax_id."""
        return await self.repo.search_by_name_or_tax_id(query, limit)


class CreatePlotOwnershipUseCase:
    """Use case for creating a PlotOwnership."""

    def __init__(
        self,
        ownership_repo: IPlotOwnershipRepository,
        land_plot_repo: ILandPlotRepository,
        event_dispatcher: EventDispatcher,
    ):
        self.ownership_repo = ownership_repo
        self.land_plot_repo = land_plot_repo
        self.event_dispatcher = event_dispatcher

    async def execute(
        self,
        land_plot_id: UUID,
        data: PlotOwnershipCreate,
        cooperative_id: UUID,
    ) -> PlotOwnership:
        """Create a new plot ownership."""
        # Verify land plot exists and belongs to cooperative
        plot = await self.land_plot_repo.get_by_id(land_plot_id, cooperative_id)
        if plot is None:
            raise ValidationError("Land plot not found")

        entity = PlotOwnership(
            id=uuid.uuid4(),
            land_plot_id=land_plot_id,
            owner_id=data.owner_id,
            share_numerator=data.share_numerator,
            share_denominator=data.share_denominator,
            is_primary=data.is_primary,
            valid_from=data.valid_from,
            valid_to=data.valid_to,
        )

        created_ownership = await self.ownership_repo.add(entity)

        # Publish domain event
        self.event_dispatcher.dispatch(
            PlotOwnershipCreated(
                ownership_id=created_ownership.id,
                land_plot_id=land_plot_id,
                owner_id=data.owner_id,
                share_numerator=data.share_numerator,
                share_denominator=data.share_denominator,
                is_primary=data.is_primary,
            )
        )

        return created_ownership


class ClosePlotOwnershipUseCase:
    """Use case for closing a PlotOwnership (setting valid_to)."""

    def __init__(
        self,
        ownership_repo: IPlotOwnershipRepository,
        event_dispatcher: EventDispatcher,
    ):
        self.ownership_repo = ownership_repo
        self.event_dispatcher = event_dispatcher

    async def execute(
        self,
        ownership_id: UUID,
        valid_to: date,
        cooperative_id: UUID | None,
    ) -> PlotOwnership | None:
        """Close plot ownership by setting valid_to date."""
        if cooperative_id is None:
            entity = await self.ownership_repo.get_by_id_any_cooperative(ownership_id)
        else:
            entity = await self.ownership_repo.get_by_id(ownership_id, cooperative_id)
        if entity is None:
            return None

        entity.valid_to = valid_to
        updated_ownership = await self.ownership_repo.update(entity)

        # Publish domain event
        self.event_dispatcher.dispatch(
            PlotOwnershipTransferred(
                ownership_id=ownership_id,
                land_plot_id=entity.land_plot_id,
                previous_owner_id=entity.owner_id,
                valid_to=valid_to.isoformat(),
            )
        )

        return updated_ownership


class GetPlotOwnershipUseCase:
    """Use case for getting PlotOwnership by ID."""

    def __init__(self, repo: IPlotOwnershipRepository):
        self.repo = repo

    async def execute(self, ownership_id: UUID, cooperative_id: UUID) -> PlotOwnership | None:
        """Get plot ownership by ID."""
        return await self.repo.get_by_id(ownership_id, cooperative_id)


class GetCurrentPlotOwnershipsUseCase:
    """Use case for getting current (non-closed) ownerships for a plot."""

    def __init__(self, repo: IPlotOwnershipRepository):
        self.repo = repo

    async def execute(self, land_plot_id: UUID) -> list[PlotOwnership]:
        """Get current ownerships for a land plot."""
        return await self.repo.get_current_ownerships(land_plot_id)
