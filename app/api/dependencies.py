from uuid import UUID
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.session import Session as SessionModel
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error = False)

CREDENTIAL_EXCEPTION = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail = "Could not validate credentials or session expired",
        headers={"WWW-Authenticate": "Bearer"},
    )

def extract_token(request: Request, token_auth: HTTPAuthorizationCredentials | None) -> str:
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token.removeprefix("Bearer ").strip()
    if token_auth:
        return token_auth.credentials
    raise CREDENTIAL_EXCEPTION

async def get_current_user(
        request: Request, 
        token_auth: HTTPAuthorizationCredentials | None = Depends(bearer_scheme), 
        db: AsyncSession = Depends(get_db)
) -> User:

        raw_token = extract_token(request, token_auth)

        payload = decode_access_token(raw_token) or {}
        try:
            user_id = UUID(str(payload.get("sub")))
            session_id = UUID(str(payload.get("session_id")))
        except (ValueError, TypeError):
            raise CREDENTIAL_EXCEPTION

        query = (select(User).join(SessionModel, SessionModel.user_id == User.id)
                .where(
                    User.id == user_id,
                    User.is_active.is_(True),
                    SessionModel.id == session_id,
                    SessionModel.expires_at > datetime.now(timezone.utc),
                )
        )

        result = await db.execute(query)
        user = result.scalars().first()

        if not user:
            raise CREDENTIAL_EXCEPTION

        return user


__all__ = ["get_db", "get_current_user"]