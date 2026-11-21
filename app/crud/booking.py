import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.booking import Booking
from app.models.booking_resource import BookingResource
from app.models.booking_series import BookingSeries
from app.schemas.booking import BookingCreate, BookingUpdate


class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):
    def _base_detail_query(self):
        return select(self.model).options(
            selectinload(self.model.sport),
            selectinload(self.model.booking_resources).selectinload(
                BookingResource.resource
            ),
            selectinload(self.model.payments),
            selectinload(self.model.booking_series).selectinload(
                BookingSeries.payments
            ),
        )

    async def get_with_details(
        self, db: AsyncSession, *, booking_id: uuid.UUID
    ) -> Optional[Booking]:
        result = await db.execute(
            self._base_detail_query().where(self.model.id == booking_id)
        )
        return result.scalars().first()

    async def get_multi_filtered(
        self,
        db: AsyncSession,
        *,
        user_id: Optional[uuid.UUID] = None,
        sport_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        start_from: Optional[datetime] = None,
        start_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Booking]:
        query = self._base_detail_query()

        if user_id is not None:
            query = query.where(self.model.user_id == user_id)
        if sport_id is not None:
            query = query.where(self.model.sport_id == sport_id)
        if status is not None:
            query = query.where(self.model.status == status.strip().lower())
        if start_from is not None:
            query = query.where(self.model.start_at >= start_from)
        if start_to is not None:
            query = query.where(self.model.start_at <= start_to)

        query = query.order_by(self.model.start_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

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

    async def expire_unpaid_bookings(
        self, db: AsyncSession, *, now_utc: datetime
    ) -> int:
        expired_ids_res = await db.execute(
            select(self.model.id).where(
                self.model.status == "pending",
                self.model.expired_at.is_not(None),
                self.model.expired_at <= now_utc,
            )
        )
        expired_ids = list(expired_ids_res.scalars().all())
        if not expired_ids:
            return 0

        await db.execute(
            update(self.model)
            .where(self.model.id.in_(expired_ids))
            .values(status="expired")
        )
        await db.execute(
            update(BookingResource)
            .where(BookingResource.booking_id.in_(expired_ids))
            .values(is_active=False)
        )
        return len(expired_ids)

    async def complete_past_bookings(
        self, db: AsyncSession, *, now_utc: datetime
    ) -> int:
        result = await db.execute(
            update(self.model)
            .where(
                self.model.status == "confirmed",
                self.model.end_at <= now_utc,
            )
            .values(status="completed")
            .returning(self.model.id)
        )
        return len(result.scalars().all())


crud_booking = CRUDBooking(Booking)
