"""FastAPI routes for meters module."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.modules.administration.domain.entities import AppUser
from app.modules.deps import (
    get_add_meter_reading_use_case,
    get_create_meter_use_case,
    get_delete_meter_use_case,
    get_get_meter_use_case,
    get_meter_readings_use_case,
    get_meters_by_owner_use_case,
    get_update_meter_use_case,
)

from .schemas import MeterCreate, MeterInDB, MeterReadingCreate, MeterReadingInDB, MeterUpdate

router = APIRouter()


@router.get(
    "/",
    response_model=list[MeterInDB],
    summary="Счётчики товарищества",
    description="Получить список всех счётчиков товарищества.",
)
async def get_meters(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    owner_id: UUID | None = None,
    use_case=Depends(get_meters_by_owner_use_case),
) -> list[MeterInDB]:
    """Get all meters for cooperative or filtered by owner."""
    if owner_id is not None:
        meters = await use_case.execute(
            owner_id=owner_id, cooperative_id=current_user.cooperative_id
        )
    else:
        # For admin users without cooperative_id, return empty list
        # Admin should query by owner_id instead
        if current_user.cooperative_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin users must specify owner_id parameter",
            )
        # Get all meters for cooperative using repository directly
        from app.api.deps import get_db
        from app.modules.meters.infrastructure.repositories import MeterRepository

        db = await anext(get_db())
        repo = MeterRepository(db)
        meters = await repo.get_all(current_user.cooperative_id)

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


@router.post(
    "/",
    response_model=MeterInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Создать счётчик",
    description="Создать новый прибор учёта. Доступно: treasurer, admin.",
)
async def create_meter(
    meter_data: MeterCreate,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_create_meter_use_case),
) -> MeterInDB:
    """Create a new meter."""
    try:
        meter = await use_case.execute(data=meter_data, cooperative_id=current_user.cooperative_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

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
    use_case=Depends(get_get_meter_use_case),
) -> MeterInDB:
    """Get meter by ID."""
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
    use_case=Depends(get_meters_by_owner_use_case),
) -> list[MeterInDB]:
    """Get all meters for an owner."""
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
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_update_meter_use_case),
) -> MeterInDB:
    """Update meter."""
    meter = await use_case.execute(
        meter_id=meter_id, data=meter_data, cooperative_id=current_user.cooperative_id
    )

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
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_delete_meter_use_case),
) -> None:
    """Delete meter."""
    deleted = await use_case.execute(meter_id=meter_id, cooperative_id=current_user.cooperative_id)

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
    current_user: Annotated[AppUser, Depends(get_current_user)],
    use_case=Depends(get_add_meter_reading_use_case),
) -> MeterReadingInDB:
    """Add a meter reading."""
    # Override meter_id from path
    reading_data.meter_id = meter_id

    try:
        reading = await use_case.execute(
            data=reading_data, cooperative_id=current_user.cooperative_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Handle duplicate reading date
        if "UNIQUE constraint" in str(e) or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Показание с такой датой уже существует",
            )
        raise

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
    use_case=Depends(get_meter_readings_use_case),
) -> list[MeterReadingInDB]:
    """Get all readings for a meter."""
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
