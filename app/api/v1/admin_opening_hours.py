import uuid
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_db
from app.core.rate_limiter import limiter
from app.models.operating_hour import OperatingHour
from app.schemas.operating_hour import OperatingHourResponse, WeeklyOperatingHoursUpdate
from app.services import operating_hour_service

router = APIRouter(prefix="/opening-hours", tags=["Admin - Opening Hours"])


@router.put("/{sport_id}", response_model=list[OperatingHourResponse])
@limiter.limit("20/minute")
async def update_weekly_opening_hours(
    request: Request,
    response: Response,
    sport_id: uuid.UUID,
    schedule_in: WeeklyOperatingHoursUpdate,
    db: AsyncSession = Depends(get_db),
) -> list[OperatingHour]:
    return await operating_hour_service.set_weekly_operating_hours(
        db=db, sport_id=sport_id, schedule_in=schedule_in, request=request
    )
