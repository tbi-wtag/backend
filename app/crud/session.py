import uuid
from datetime import datetime, timezone
from app.models.session import Session as SessionModel
from app.models.user import User
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession


async def delete_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> None:
    await db.execute(delete(SessionModel).where(SessionModel.user_id == user_id))
    await db.flush()


async def create_session(
    db: AsyncSession, user_id: uuid.UUID, expires_at: datetime
) -> SessionModel:
    db_session = SessionModel(
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(db_session)
    await db.flush()
    return db_session


async def get_session_by_id(
    db: AsyncSession, session_id: uuid.UUID
) -> SessionModel | None:
    result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    return result.scalars().first()


async def get_active_user_by_session(
    db: AsyncSession, session_id: uuid.UUID
) -> User | None:
    query = (
        select(User)
        .join(SessionModel, SessionModel.user_id == User.id)
        .where(
            User.is_active.is_(True),
            SessionModel.id == session_id,
            SessionModel.expires_at > datetime.now(timezone.utc),
        )
    )
    result = await db.execute(query)
    return result.scalars().first()
