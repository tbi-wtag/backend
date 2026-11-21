import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.resource_block import ResourceBlock
from app.schemas.resource_block import ResourceBlockCreate


class CRUDResourceBlock(
    CRUDBase[ResourceBlock, ResourceBlockCreate, ResourceBlockCreate]
):
    async def get_overlapping_for_resource(
        self,
        db: AsyncSession,
        *,
        resource_id: uuid.UUID,
        start_at: datetime,
        end_at: datetime,
    ) -> list[ResourceBlock]:
        result = await db.execute(
            select(self.model)
            .where(
                self.model.resource_id == resource_id,
                self.model.start_at < end_at,
                self.model.end_at > start_at,
            )
            .order_by(self.model.start_at.asc())
        )
        return list(result.scalars().all())

    async def get_overlapping_for_resources(
        self,
        db: AsyncSession,
        *,
        resource_ids: list[uuid.UUID],
        start_at: datetime,
        end_at: datetime,
    ) -> list[ResourceBlock]:
        if not resource_ids:
            return []
        result = await db.execute(
            select(self.model)
            .where(
                self.model.resource_id.in_(resource_ids),
                self.model.start_at < end_at,
                self.model.end_at > start_at,
            )
            .order_by(self.model.start_at.asc())
        )
        return list(result.scalars().all())

    async def get_multi_filtered(
        self,
        db: AsyncSession,
        *,
        resource_id: Optional[uuid.UUID] = None,
        start_at: Optional[datetime] = None,
        end_at: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ResourceBlock]:
        query = select(self.model)

        if resource_id is not None:
            query = query.where(self.model.resource_id == resource_id)
        if start_at is not None:
            query = query.where(self.model.end_at > start_at)
        if end_at is not None:
            query = query.where(self.model.start_at < end_at)

        query = query.order_by(self.model.start_at.asc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())


crud_resource_block = CRUDResourceBlock(ResourceBlock)
