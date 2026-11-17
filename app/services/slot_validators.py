import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.booking import crud_booking
from app.crud.operating_hour import crud_operating_hour
from app.crud.resource import crud_resource
from app.crud.resource_block import crud_resource_block
from app.models.resource import Resource
from app.models.sport import Sport
from app.services import sport_service


async def get_day_bounds(
    db: AsyncSession, sport_id: uuid.UUID, target_date: date
) -> Optional[tuple[datetime, datetime]]:
    operating_hours = await crud_operating_hour.get_by_sport_and_weekday(
        db, sport_id=sport_id, weekday=target_date.weekday()
    )
    if operating_hours is None:
        return None

    return (
        datetime.combine(target_date, operating_hours.open_time, tzinfo=timezone.utc),
        datetime.combine(target_date, operating_hours.close_time, tzinfo=timezone.utc),
    )


async def get_unavailable_map(
    db: AsyncSession,
    resource_ids: list[uuid.UUID],
    start_utc: datetime,
    end_utc: datetime,
    now_utc: datetime,
) -> dict[uuid.UUID, list[tuple[datetime, datetime]]]:
    unavailable: dict[uuid.UUID, list[tuple[datetime, datetime]]] = {
        resource_id: [] for resource_id in resource_ids
    }
    if not resource_ids:
        return unavailable

    blocks = await crud_resource_block.get_overlapping_for_resources(
        db, resource_ids=resource_ids, start_at=start_utc, end_at=end_utc
    )
    bookings = await crud_booking.get_overlapping_booking_resources(
        db,
        resource_ids=resource_ids,
        start_at=start_utc,
        end_at=end_utc,
        now_utc=now_utc,
    )
    for item in (*blocks, *bookings):
        unavailable[item.resource_id].append((item.start_at, item.end_at))

    return unavailable


def is_free(
    intervals: list[tuple[datetime, datetime]], start: datetime, end: datetime
) -> bool:
    return all(
        interval_end <= start or interval_start >= end
        for interval_start, interval_end in intervals
    )


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


async def resolve_and_validate_resources(
    db: AsyncSession,
    *,
    sport_id: uuid.UUID,
    start_at: datetime,
    duration_minutes: int,
    number_of_people: int,
    resource_ids: Optional[list[uuid.UUID]] = None,
    pitch_format: Optional[str] = None,
    surface: Optional[str] = None,
) -> tuple[list[Resource], datetime, datetime]:
    if number_of_people <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="number_of_people must be greater than zero.",
        )

    slot_start, slot_end = await validate_slot_window(
        db,
        sport_id=sport_id,
        start_at=start_at,
        duration_minutes=duration_minutes,
    )
    now_utc = datetime.now(timezone.utc)

    candidates = await crud_resource.get_by_sport_filtered(
        db,
        sport_id=sport_id,
        is_active=True,
        pitch_format=pitch_format,
        surface=surface,
    )
    unavailable = await get_unavailable_map(
        db, [resource.id for resource in candidates], slot_start, slot_end, now_utc
    )

    resources_by_id = {resource.id: resource for resource in candidates}
    available = [
        resource
        for resource in candidates
        if is_free(unavailable[resource.id], slot_start, slot_end)
    ]
    selected_ids = list(dict.fromkeys(resource_ids or []))

    if selected_ids:
        if any(resource_id not in resources_by_id for resource_id in selected_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more selected resources are invalid or inactive.",
            )
        selected = [resources_by_id[resource_id] for resource_id in selected_ids]
        for resource in selected:
            if not is_free(unavailable[resource.id], slot_start, slot_end):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Resource '{resource.resource_name}' is not available for this slot.",
                )
    else:
        if not available:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No matching resources are available for this slot.",
            )
        single_fit = next(
            (
                resource
                for resource in available
                if resource.capacity >= number_of_people
            ),
            None,
        )
        selected = [single_fit] if single_fit is not None else []
        if single_fit is None:
            selected_capacity = 0
            for resource in available:
                selected.append(resource)
                selected_capacity += resource.capacity
                if selected_capacity >= number_of_people:
                    break

    selected_capacity = sum(resource.capacity for resource in selected)
    if selected_capacity < number_of_people:
        message = (
            "Selected resources do not have enough capacity."
            if selected_ids
            else f"Available resources only support up to {selected_capacity} people."
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    return selected, slot_start, slot_end
