from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.models.session import Session as SessionModel
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, TokenResponse
from app.schemas.session import SessionResponse
from app.schemas.user import UserResponse


async def login_user(db: AsyncSession, credentials: LoginRequest) -> LoginResponse:
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalars().first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    await db.execute(delete(SessionModel).where(SessionModel.user_id == user.id))
    await db.flush()  


    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt.access_token_expire_minutes
    )
    db_session = SessionModel(
        user_id=user.id,
        expires_at=expires_at,
    )

    db.add(db_session)
    await db.flush()  

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