import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.resource import Resource
from app.schemas.resource import ResourceCreate, ResourceUpdate


class CRUDResource(CRUDBase[Resource, ResourceCreate, ResourceUpdate]):

    async def get_by_sport_and_name(
        self, db: AsyncSession, *, sport_id: uuid.UUID, resource_name: str
    ) -> Optional[Resource]:
        result = await db.execute(
            select(self.model).where(
                self.model.sport_id == sport_id,
                self.model.resource_name.ilike(resource_name.strip()),
            )
        )
        return result.scalars().first()

    async def count_by_sport(
        self, db: AsyncSession, *, sport_id: uuid.UUID, is_active: Optional[bool] = True
    ) -> int:
        query = select(func.count(self.model.id)).where(self.model.sport_id == sport_id)
        if is_active is not None:
            query = query.where(self.model.is_active == is_active)
        result = await db.execute(query)
        return result.scalar_one()

    async def get_by_sport_filtered(
        self,
        db: AsyncSession,
        *,
        sport_id: uuid.UUID,
        is_active: Optional[bool] = True,
        pitch_format: Optional[str] = None,
        surface: Optional[str] = None,
        min_capacity: Optional[int] = None,
        max_price: Optional[Decimal] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Resource]:
        query = select(self.model).where(self.model.sport_id == sport_id)

        if is_active is not None:
            query = query.where(self.model.is_active == is_active)
        if pitch_format:
            query = query.where(self.model.pitch_format.ilike(pitch_format.strip()))
        if surface:
            query = query.where(self.model.surface.ilike(surface.strip()))
        if min_capacity is not None:
            query = query.where(self.model.capacity >= min_capacity)
        if max_price is not None:
            query = query.where(self.model.price_per_hour <= max_price)

        query = query.order_by(self.model.resource_name).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())


crud_resource = CRUDResource(Resource)
