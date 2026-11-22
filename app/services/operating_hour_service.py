import uuid
from typing import Optional
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.operating_hour import crud_operating_hour
from app.models.operating_hour import OperatingHour
from app.schemas.operating_hour import WeeklyOperatingHoursUpdate
from app.services import sport_service
from app.services.audit_service import audit_service


async def get_operating_hours_by_sport(
    db: AsyncSession, *, sport_id: uuid.UUID
) -> list[OperatingHour]:
    await sport_service.get_sport_by_id(db, sport_id=sport_id)
    return await crud_operating_hour.get_by_sport(db, sport_id=sport_id)


async def set_weekly_operating_hours(
    db: AsyncSession,
    *,
    sport_id: uuid.UUID,
    schedule_in: WeeklyOperatingHoursUpdate,
    request: Optional[Request] = None,
) -> list[OperatingHour]:
    sport = await sport_service.get_sport_by_id(db, sport_id=sport_id)

    hours = await crud_operating_hour.replace_for_sport(
        db,
        sport_id=sport.id,
        schedule=schedule_in.schedule,
        flush=True,
    )

    await audit_service.log_event(
        db=db,
        action="OPERATING_HOURS_UPDATE",
        request=request,
        status="SUCCESS",
        details={
            "sport_id": str(sport.id),
            "sport_name": sport.sport_name,
            "weekdays_configured": [item.weekday for item in schedule_in.schedule],
        },
        flush=True,
    )

    await db.commit()
    return await crud_operating_hour.get_by_sport(db, sport_id=sport.id)
