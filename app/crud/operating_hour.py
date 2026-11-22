import uuid
from typing import Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.operating_hour import OperatingHour
from app.schemas.operating_hour import OperatingHourCreate, OperatingHourUpdate


class CRUDOperatingHour(
    CRUDBase[OperatingHour, OperatingHourCreate, OperatingHourUpdate]
):
    async def get_by_sport(
        self, db: AsyncSession, *, sport_id: uuid.UUID
    ) -> list[OperatingHour]:
        result = await db.execute(
            select(self.model)
            .where(self.model.sport_id == sport_id)
            .order_by(self.model.weekday.asc())
        )
        return list(result.scalars().all())

    async def get_by_sport_and_weekday(
        self, db: AsyncSession, *, sport_id: uuid.UUID, weekday: int
    ) -> Optional[OperatingHour]:
        result = await db.execute(
            select(self.model).where(
                self.model.sport_id == sport_id,
                self.model.weekday == weekday,
            )
        )
        return result.scalars().first()

    async def replace_for_sport(
        self,
        db: AsyncSession,
        *,
        sport_id: uuid.UUID,
        schedule: list[OperatingHourCreate],
        flush: bool = False,
    ) -> list[OperatingHour]:
        await db.execute(delete(self.model).where(self.model.sport_id == sport_id))
        await db.flush()

        new_rows = [
            self.model(
                sport_id=sport_id,
                weekday=item.weekday,
                open_time=item.open_time,
                close_time=item.close_time,
            )
            for item in schedule
        ]
        db.add_all(new_rows)

        if flush:
            await db.flush()
        else:
            await db.commit()

        return await self.get_by_sport(db, sport_id=sport_id)


crud_operating_hour = CRUDOperatingHour(OperatingHour)
