from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.app_user import AppUser
from app.schemas.meter import MeterCreate, MeterInDB, MeterReadingCreate, MeterReadingInDB
from app.services import meter_service

router = APIRouter()


@router.get(
    "/",
    response_model=list[MeterInDB],
    summary="Список счётчиков",
    description="Получить список приборов учёта (вода, электричество) по владельцу.",
)
async def get_meters(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    owner_id: UUID | None = Query(None, description="Фильтр по владельцу"),
) -> list[MeterInDB]:
    """
    Получить список счётчиков.

    - **admin**: может указать любой owner_id
    - **chairman/treasurer**: видят только счётчики владельцев своего СТ
    """
    if owner_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать owner_id",
        )

    meters = await meter_service.get_meters_by_owner(db, owner_id)
    return meters


@router.get(
    "/{meter_id}",
    response_model=MeterInDB,
    summary="Получить счётчик",
    description="Получить информацию о приборе учёта по ID.",
)
async def get_meter(
    meter_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> MeterInDB:
    """Получить счётчик по ID."""
    meter = await meter_service.get_meter(db, meter_id)
    if meter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Счётчик не найден",
        )
    return meter


@router.post(
    "/",
    response_model=MeterInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Создать счётчик",
    description="Создать новый прибор учёта (вода или электричество). При создании автоматически создаётся FinancialSubject. Доступно: treasurer, admin.",
)
async def create_meter(
    meter_data: MeterCreate,
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    db: AsyncSession = Depends(get_db),
) -> MeterInDB:
    """Создать счётчик (treasurer, admin). При создании автоматически создаётся FinancialSubject."""
    try:
        meter = await meter_service.create_meter(db, meter_data)
        return meter
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{meter_id}/readings",
    response_model=MeterReadingInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить показание счётчика",
    description="Добавить новое показание прибора учёта. Доступно: treasurer, admin.",
)
async def add_meter_reading(
    meter_id: UUID,
    reading_data: MeterReadingCreate,
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    db: AsyncSession = Depends(get_db),
) -> MeterReadingInDB:
    """Добавить показание счётчика (treasurer, admin)."""
    # Проверка что счётчик существует
    meter = await meter_service.get_meter(db, meter_id)
    if meter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Счётчик не найден",
        )

    # Устанавливаем meter_id из пути
    reading_data.meter_id = meter_id

    try:
        reading = await meter_service.add_meter_reading(db, reading_data)
        return reading
    except Exception as e:
        # Обработка уникальности (meter_id, reading_date)
        if "unique" in str(e).lower() or "uq_meter_readings" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Показание на эту дату уже существует",
            )
        raise


@router.get(
    "/{meter_id}/readings",
    response_model=list[MeterReadingInDB],
    summary="История показаний счётчика",
    description="Получить историю всех показаний прибора учёта.",
)
async def get_meter_readings(
    meter_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[MeterReadingInDB]:
    """Получить историю показаний счётчика."""
    readings = await meter_service.get_meter_readings(db, meter_id)
    return readings
