import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sport import Sport
from app.services import sport_service
from app.services.slot_availability import get_day_bounds


def validate_duration(sport: Sport, duration_minutes: int) -> None:
    if not sport.min_hours * 60 <= duration_minutes <= sport.max_hours * 60:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Booking duration must be between {sport.min_hours} and "
                f"{sport.max_hours} hours for this sport."
            ),
        )


async def validate_slot_window(
    db: AsyncSession,
    *,
    sport_id: uuid.UUID,
    start_at: datetime,
    duration_minutes: int,
) -> tuple[datetime, datetime]:
    sport = await sport_service.get_sport_by_id(db, sport_id=sport_id)
    validate_duration(sport, duration_minutes)

    slot_start = (
        start_at.replace(tzinfo=timezone.utc)
        if start_at.tzinfo is None
        else start_at.astimezone(timezone.utc)
    )
    slot_end = slot_start + timedelta(minutes=duration_minutes)

    if slot_start.minute or slot_start.second or slot_start.microsecond:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bookings must start on the hour.",
        )
    if slot_start <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot book slots in the past.",
        )
    if slot_start.date() != slot_end.date():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bookings cannot span across midnight.",
        )

    bounds = await get_day_bounds(db, sport_id, slot_start.date())
    if bounds is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The facility is closed for this sport on the selected day.",
        )

    open_at, close_at = bounds
    if slot_start < open_at or slot_end > close_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Requested time must be within operating hours "
                f"({open_at:%H:%M} - {close_at:%H:%M})."
            ),
        )

    return slot_start, slot_end


