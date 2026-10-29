from uuid import UUID
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token, extract_token
from app.db.session import get_db
from app.models.user import User
from app.crud import session as crud_session

CREDENTIAL_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials or session expired",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:

    raw_token = extract_token(request)
    if not raw_token:
        raise CREDENTIAL_EXCEPTION

    payload = decode_access_token(raw_token)
    if not payload:
        raise CREDENTIAL_EXCEPTION

    try:
        user_id = UUID(str(payload.get("sub")))
        session_id = UUID(str(payload["session_id"]))
    except KeyError, ValueError, TypeError:
        raise CREDENTIAL_EXCEPTION

    user = await crud_session.get_active_user_by_session(
        db, user_id=user_id, session_id=session_id
    )
    if not user:
        raise CREDENTIAL_EXCEPTION

    return user
