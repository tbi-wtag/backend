import uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.models.session import Session as SessionModel
from app.schemas.auth import LoginRequest, LoginResponse, TokenResponse
from app.schemas.session import SessionResponse
from app.schemas.user import UserResponse
from app.crud import user as crud_user
from app.crud import session as crud_session


async def login_user(db: AsyncSession, credentials: LoginRequest) -> LoginResponse:
    user = await crud_user.get_user_by_email(db, email=credentials.email)

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    await crud_session.delete_by_user_id(db, user_id=user.id)

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt.access_token_expire_minutes
    )

    db_session = await crud_session.create_session(
        db, user_id=user.id, expires_at=expires_at
    )

    token_payload = {
        "sub": str(user.id),
        "session_id": str(db_session.id),
    }
    access_token = create_access_token(data=token_payload)

    await db.commit()
    await db.refresh(db_session)

    return LoginResponse(
        user=UserResponse.model_validate(user),
        token=TokenResponse(access_token=access_token),
        session=SessionResponse.model_validate(db_session),
    )


async def logout_user(db: AsyncSession, user_id: uuid.UUID) -> None:
    await crud_session.delete_by_user_id(db, user_id=user_id)

    await db.commit()
