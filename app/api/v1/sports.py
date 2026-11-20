import uuid
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_db
from app.core.rate_limiter import limiter
from app.models.resource import Resource
from app.models.sport import Sport
from app.schemas.resource import ResourceResponse
from app.schemas.sport import SportCreate, SportResponse, SportUpdate
from app.services import sport_service, resource_service
from app.models.operating_hour import OperatingHour
from app.schemas.operating_hour import OperatingHourResponse
from app.services import operating_hour_service

router = APIRouter(prefix="/sports", tags=["Sports"])


@router.post(
    "",
    response_model=SportResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
async def create_sport(
    request: Request,
    response: Response,
    sport_in: SportCreate,
    db: AsyncSession = Depends(get_db),
) -> Sport:
    return await sport_service.create_sport(db=db, sport_in=sport_in, request=request)


@router.get("", response_model=list[SportResponse])
async def list_sports(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    return await sport_service.get_sports(db=db, skip=skip, limit=limit)


@router.get("/{sport_id}", response_model=SportResponse)
async def get_sport(
    sport_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Sport:
    return await sport_service.get_sport_by_id(db=db, sport_id=sport_id)


@router.get("/{sport_id}/resources", response_model=list[ResourceResponse])
async def list_sport_resources(
    sport_id: uuid.UUID,
    is_active: Optional[bool] = True,
    pitch_format: Optional[str] = None,
    surface: Optional[str] = None,
    min_capacity: Optional[int] = None,
    max_price: Optional[Decimal] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> list[Resource]:
    return await resource_service.get_resources_by_sport(
        db=db,
        sport_id=sport_id,
        is_active=is_active,
        pitch_format=pitch_format,
        surface=surface,
        min_capacity=min_capacity,
        max_price=max_price,
        skip=skip,
        limit=limit,
    )


@router.get("/{sport_id}/opening-hours", response_model=list[OperatingHourResponse])
async def get_sport_opening_hours(
    sport_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[OperatingHour]:
    return await operating_hour_service.get_operating_hours_by_sport(
        db=db, sport_id=sport_id
    )


@router.patch("/{sport_id}", response_model=SportResponse)
@limiter.limit("20/minute")
async def update_sport(
    request: Request,
    response: Response,
    sport_id: uuid.UUID,
    sport_in: SportUpdate,
    db: AsyncSession = Depends(get_db),
) -> Sport:
    return await sport_service.update_sport(
        db=db, sport_id=sport_id, sport_in=sport_in, request=request
    )


@router.delete("/{sport_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_sport(
    request: Request,
    response: Response,
    sport_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    await sport_service.delete_sport(db=db, sport_id=sport_id, request=request)
