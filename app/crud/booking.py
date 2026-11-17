import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.booking import Booking
from app.models.booking_resource import BookingResource


class CRUDBooking(CRUDBase[Booking, Any, Any]):
    async def get_overlapping_booking_resources(
        self,
        db: AsyncSession,
        *,
        resource_ids: list[uuid.UUID],
        start_at: datetime,
        end_at: datetime,
        now_utc: datetime,
    ) -> list[BookingResource]:
        if not resource_ids:
            return []
        result = await db.execute(
            select(BookingResource)
            .join(Booking, Booking.id == BookingResource.booking_id)
            .where(
                BookingResource.resource_id.in_(resource_ids),
                BookingResource.is_active.is_(True),
                BookingResource.start_at < end_at,
                BookingResource.end_at > start_at,
                or_(
                    Booking.status == "confirmed",
                    and_(
                        Booking.status == "pending",
                        Booking.expired_at.is_not(None),
                        Booking.expired_at > now_utc,
                    ),
                ),
            )
        )
        return list(result.scalars().all())


crud_booking = CRUDBooking(Booking)