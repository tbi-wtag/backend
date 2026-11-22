import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.crud.base import CRUDBase
from app.models.booking import Booking
from app.models.booking_resource import BookingResource
from app.models.booking_series import BookingSeries


class CRUDBookingSeries(CRUDBase[BookingSeries, BaseModel, BaseModel]):
    def _base_detail_query(self):
        bookings_loader = selectinload(self.model.bookings)

        return select(self.model).options(
            selectinload(self.model.payments),
            bookings_loader.selectinload(Booking.sport),
            bookings_loader.selectinload(Booking.payments),
            bookings_loader.selectinload(Booking.booking_resources).selectinload(
                BookingResource.resource
            ),
        )

    async def get_with_details(
        self, db: AsyncSession, *, series_id: uuid.UUID
    ) -> Optional[BookingSeries]:
        result = await db.execute(
            self._base_detail_query().where(self.model.id == series_id)
        )
        return result.scalars().first()

    async def get_multi_filtered(
        self,
        db: AsyncSession,
        *,
        user_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[BookingSeries]:
        query = self._base_detail_query()

        if user_id is not None:
            query = query.where(self.model.user_id == user_id)

        query = query.order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())


crud_booking_series = CRUDBookingSeries(BookingSeries)
