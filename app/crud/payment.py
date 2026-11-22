import uuid
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.booking_series import BookingSeries
from app.models.payment import Payment


class CRUDPayment(CRUDBase[Payment, BaseModel, BaseModel]):
    def _base_detail_query(self):
        booking_series_loader = selectinload(self.model.booking_series)

        return select(self.model).options(
            selectinload(self.model.booking),
            booking_series_loader.selectinload(BookingSeries.bookings),
        )

    async def get_with_details(
        self, db: AsyncSession, *, payment_id: uuid.UUID
    ) -> Optional[Payment]:
        result = await db.execute(
            self._base_detail_query().where(self.model.id == payment_id)
        )
        return result.scalars().first()

    async def get_latest_by_booking_id(
        self, db: AsyncSession, *, booking_id: uuid.UUID
    ) -> Optional[Payment]:
        result = await db.execute(
            self._base_detail_query()
            .where(self.model.booking_id == booking_id)
            .order_by(self.model.created_at.desc())
        )
        return result.scalars().first()

    async def get_latest_by_series_id(
        self, db: AsyncSession, *, series_id: uuid.UUID
    ) -> Optional[Payment]:
        result = await db.execute(
            self._base_detail_query()
            .where(self.model.series_id == series_id)
            .order_by(self.model.created_at.desc())
        )
        return result.scalars().first()

    async def get_multi_filtered(
        self,
        db: AsyncSession,
        *,
        user_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Payment]:
        query = self._base_detail_query()

        if user_id is not None:
            query = query.where(self.model.user_id == user_id)
        if status is not None:
            query = query.where(self.model.status == status.strip().lower())

        query = query.order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())


crud_payment = CRUDPayment(Payment)
