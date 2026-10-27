from pathlib import Path
import uuid
import casbin
from fastapi import HTTPException, Request, status

from app.core.security import decode_access_token, extract_token
from app.schemas.auth import UserSession

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = str(BASE_DIR / "model.conf")
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
        return UserSession(
            user_id=uuid.UUID(str(payload["sub"])),
            session_id=uuid.UUID(str(payload["session_id"])),
            email = payload["email"],
            role = payload["role"]
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Malformed token payload: {str(exc)}",
        )


def check_user_privileges(role: str, api_path: str, method: str) -> None:
    is_authorized = enforcer.enforce(role, api_path, method)
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: Role '{role}' cannot execute '{method}' on '{api_path}'",
        )