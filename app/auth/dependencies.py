from pathlib import Path
from uuid import UUID
from app.models.user import User
import casbin
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token, extract_token
from app.crud.user import get_user_by_id
from app.crud.session import get_active_user_by_session
from app.db.session import AsyncSessionLocal, get_db
from app.schemas.auth import UserSession
from app.schemas.enums import UserRole

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = str(BASE_DIR / "rbac_model.conf")
POLICY_PATH = str(BASE_DIR / "policy.csv")

enforcer = casbin.Enforcer(MODEL_PATH, POLICY_PATH)


async def get_current_user_for_middleware(request: Request) -> UserSession:
    raw_token = extract_token(request)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed authentication credentials",
        )

    payload = decode_access_token(raw_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    try:
        session_id = UUID(payload["session_id"])
    except KeyError, ValueError, TypeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing session identification in token",
        )

    async with AsyncSessionLocal() as db:
        user = await get_active_user_by_session(db, session_id=session_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired, invalid, or user inactive",
            )

        return UserSession(
            user_id=user.id,
            session_id=session_id,
            email=user.email,
            role=UserRole(user.role),
        )


def check_user_privileges(role: UserRole, api_path: str, method: str) -> None:
    is_authorized = enforcer.enforce(role.value, api_path, method)
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: Role '{role.value}' cannot execute '{method}' on '{api_path}'",
        )


def get_current_user(request: Request) -> UserSession:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated in request state",
        )
    return user


async def get_current_user_from_db(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    user_session: UserSession = get_current_user(request)

    user = await get_user_by_id(db, user_id=user_session.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user
