"""FastAPI routes for meters module."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.app_user import AppUser

from .schemas import MeterCreate, MeterInDB, MeterUpdate, MeterReadingCreate, MeterReadingInDB
from ..infrastructure.repositories import MeterRepository, MeterReadingRepository
from ..application.use_cases import (
    CreateMeterUseCase,
    GetMeterUseCase,
    GetMetersByOwnerUseCase,
    UpdateMeterUseCase,
    DeleteMeterUseCase,
    AddMeterReadingUseCase,
    GetMeterReadingsUseCase,
)

router = APIRouter()


def _get_meter_repo(db: AsyncSession) -> MeterRepository:
    return MeterRepository(db)


def _get_meter_reading_repo(db: AsyncSession) -> MeterReadingRepository:
    return MeterReadingRepository(db)


@router.post(
    "/",
    response_model=MeterInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Создать счётчик",
    description="Создать новый прибор учёта. Доступно: treasurer, admin.",
)
async def create_meter(
    meter_data: MeterCreate,
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    db: AsyncSession = Depends(get_db),
) -> MeterInDB:
    """Create a new meter."""
    repo = _get_meter_repo(db)
    use_case = CreateMeterUseCase(repo)
    
    meter = await use_case.execute(data=meter_data, cooperative_id=current_user.cooperative_id)
    
    return MeterInDB(
        id=meter.id,
        owner_id=meter.owner_id,
        meter_type=meter.meter_type,
        serial_number=meter.serial_number,
        installation_date=meter.installation_date,
        status=meter.status,
        created_at=meter.created_at,
        updated_at=meter.updated_at,
    )


@router.get(
    "/{meter_id}",
    response_model=MeterInDB,
    summary="Получить счётчик",
    description="Получить информацию о счётчике по ID.",
)
async def get_meter(
    meter_id: UUID,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> MeterInDB:
    """Get meter by ID."""
    repo = _get_meter_repo(db)
    use_case = GetMeterUseCase(repo)
    
    meter = await use_case.execute(meter_id=meter_id, cooperative_id=current_user.cooperative_id)
    
    if meter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Счётчик не найден")
    
    return MeterInDB(
        id=meter.id,
        owner_id=meter.owner_id,
        meter_type=meter.meter_type,
        serial_number=meter.serial_number,
        installation_date=meter.installation_date,
        status=meter.status,
        created_at=meter.created_at,
        updated_at=meter.updated_at,
    )


@router.get(
    "/owner/{owner_id}",
    response_model=list[MeterInDB],
    summary="Счётчики владельца",
    description="Получить список счётчиков владельца.",
)
async def get_meters_by_owner(
    owner_id: UUID,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> list[MeterInDB]:
    """Get all meters for an owner."""
    repo = _get_meter_repo(db)
    use_case = GetMetersByOwnerUseCase(repo)
    
    meters = await use_case.execute(owner_id=owner_id, cooperative_id=current_user.cooperative_id)
    
    return [
        MeterInDB(
            id=m.id,
            owner_id=m.owner_id,
            meter_type=m.meter_type,
            serial_number=m.serial_number,
            installation_date=m.installation_date,
            status=m.status,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
        for m in meters
    ]


@router.patch(
    "/{meter_id}",
    response_model=MeterInDB,
    summary="Обновить счётчик",
    description="Обновить информацию о счётчике. Доступно: treasurer, admin.",
)
async def update_meter(
    meter_id: UUID,
    meter_data: MeterUpdate,
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    db: AsyncSession = Depends(get_db),
) -> MeterInDB:
    """Update meter."""
    repo = _get_meter_repo(db)
    use_case = UpdateMeterUseCase(repo)
    
    meter = await use_case.execute(meter_id=meter_id, data=meter_data, cooperative_id=current_user.cooperative_id)
    
    if meter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Счётчик не найден")
    
    return MeterInDB(
        id=meter.id,
        owner_id=meter.owner_id,
        meter_type=meter.meter_type,
        serial_number=meter.serial_number,
        installation_date=meter.installation_date,
        status=meter.status,
        created_at=meter.created_at,
        updated_at=meter.updated_at,
    )


@router.delete(
    "/{meter_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить счётчик",
    description="Удалить счётчик. Доступно только admin.",
)
async def delete_meter(
    meter_id: UUID,
    _: Annotated[AppUser, Depends(require_role(["admin"]))],
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete meter."""
    repo = _get_meter_repo(db)
    use_case = DeleteMeterUseCase(repo)
    
    deleted = await use_case.execute(meter_id=meter_id, cooperative_id=_.cooperative_id)
    
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Счётчик не найден")


@router.post(
    "/{meter_id}/readings",
    response_model=MeterReadingInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить показание",
    description="Добавить показание счётчика. Доступно: treasurer, admin.",
)
async def add_meter_reading(
    meter_id: UUID,
    reading_data: MeterReadingCreate,
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    db: AsyncSession = Depends(get_db),
) -> MeterReadingInDB:
    """Add a meter reading."""
    # Override meter_id from path
    reading_data.meter_id = meter_id
    
    repo = _get_meter_reading_repo(db)
    use_case = AddMeterReadingUseCase(repo)
    
    reading = await use_case.execute(data=reading_data)
    
    return MeterReadingInDB(
        id=reading.id,
        meter_id=reading.meter_id,
        reading_value=reading.reading_value,
        reading_date=reading.reading_date,
        created_at=reading.created_at,
    )


@router.get(
    "/{meter_id}/readings",
    response_model=list[MeterReadingInDB],
    summary="Показания счётчика",
    description="Получить историю показаний счётчика.",
)
async def get_meter_readings(
    meter_id: UUID,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> list[MeterReadingInDB]:
    """Get all readings for a meter."""
    repo = _get_meter_reading_repo(db)
    use_case = GetMeterReadingsUseCase(repo)
    
    readings = await use_case.execute(meter_id=meter_id)
    
    return [
        MeterReadingInDB(
            id=r.id,
            meter_id=r.meter_id,
            reading_value=r.reading_value,
            reading_date=r.reading_date,
            created_at=r.created_at,
        )
        for r in readings
    ]
