import uuid
from datetime import datetime, timezone
from typing import Optional
from app.models.session import Session as SessionModel
from app.models.user import User
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.schemas.session import SessionCreate, SessionUpdate


class CRUDSession(CRUDBase[SessionModel, SessionCreate, SessionUpdate]):

    async def create_session(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        expires_at: datetime,
        flush: bool = True,
    ) -> SessionModel:
        session_in = SessionCreate(user_id=user_id, expires_at=expires_at)
        return await self.create(db, obj_in=session_in, flush=flush)

    async def delete_by_user_id(
        self, db: AsyncSession, *, user_id: uuid.UUID, flush: bool = True
    ) -> None:
        await db.execute(delete(self.model).where(self.model.user_id == user_id))

        if flush:
            await db.flush()
        else:
            await db.commit()

    async def get_active_user_by_session(
        self, db: AsyncSession, *, session_id: uuid.UUID | str
    ) -> Optional[User]:
        query = (
            select(User)
            .join(self.model, self.model.user_id == User.id)
            .where(
                User.is_active.is_(True),
                self.model.id == session_id,
                self.model.expires_at > datetime.now(timezone.utc),
            )
        )

        result = await db.execute(query)
        return result.scalars().first()


crud_session = CRUDSession(SessionModel)
