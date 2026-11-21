import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.booking import crud_booking
from app.crud.operating_hour import crud_operating_hour
from app.crud.resource_block import crud_resource_block


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
