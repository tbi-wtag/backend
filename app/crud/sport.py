from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.sport import Sport
from app.schemas.sport import SportCreate, SportUpdate


class CRUDSport(CRUDBase[Sport, SportCreate, SportUpdate]):

    async def get_by_name(
        self, db: AsyncSession, *, sport_name: str
    ) -> Optional[Sport]:
        result = await db.execute(
            select(self.model).where(self.model.sport_name.ilike(sport_name.strip()))
        )
        return result.scalars().first()


crud_sport = CRUDSport(Sport)
