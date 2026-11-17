import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.resource import crud_resource
from app.schemas.slot import (
    AvailableResourceResponse,
    AvailableSlotResponse,
    SlotSearchResponse,
)
from app.services import sport_service
from app.services.slot_validators import (
    get_day_bounds,
    get_unavailable_map,
    is_free,
    resolve_and_validate_resources,
    validate_duration,
)


async def search_available_slots(
    db: AsyncSession,
    *,
    sport_id: uuid.UUID,
    search_date: date,
    duration_minutes: Optional[int] = None,
    pitch_format: Optional[str] = None,
    surface: Optional[str] = None,
) -> SlotSearchResponse:
    sport = await sport_service.get_sport_by_id(db, sport_id=sport_id)
    if duration_minutes is None:
        duration_minutes = settings.booking.default_slot_duration_minutes
    validate_duration(sport, duration_minutes)

    bounds = await get_day_bounds(db, sport_id, search_date)
    if bounds is None:
        return SlotSearchResponse(
            sport_id=sport_id,
            search_date=search_date,
            duration_minutes=duration_minutes,
            slots=[],
        )

    open_at, close_at = bounds
    candidates = await crud_resource.get_by_sport_filtered(
        db,
        sport_id=sport_id,
        is_active=True,
        pitch_format=pitch_format,
        surface=surface,
    )
    now_utc = datetime.now(timezone.utc)
    unavailable = await get_unavailable_map(
        db,
        [resource.id for resource in candidates],
        open_at,
        close_at,
        now_utc,
    )
    step = timedelta(minutes=settings.booking.slot_step_minutes)
    duration = timedelta(minutes=duration_minutes)
    slots: list[AvailableSlotResponse] = []
    slot_start = open_at.replace(minute=0, second=0, microsecond=0)
    if slot_start < open_at:
        slot_start += timedelta(hours=1)

    while slot_start + duration <= close_at:
        slot_end = slot_start + duration
        available = [
            resource
            for resource in candidates
            if slot_start > now_utc
            and is_free(unavailable[resource.id], slot_start, slot_end)
        ]
        if available:
            slots.append(
                AvailableSlotResponse(
                    start_at=slot_start,
                    end_at=slot_end,
                    duration_minutes=duration_minutes,
                    available_resources=[
                        AvailableResourceResponse.model_validate(resource)
                        for resource in available
                    ],
                )
            )
        slot_start += step

    return SlotSearchResponse(
        sport_id=sport_id,
        search_date=search_date,
        duration_minutes=duration_minutes,
        slots=slots,
    )