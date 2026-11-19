import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.resource import crud_resource
from app.models.resource import Resource
from app.schemas.slot import (
    AvailableResourceResponse,
    AvailableSlotResponse,
    SlotSearchResponse,
)
from app.services import sport_service
from app.services.slot_availability import (
    get_day_bounds,
    get_unavailable_map,
    is_free,
)
from app.services.slot_validators import (
    validate_duration,
    validate_slot_window,
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