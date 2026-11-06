import uuid
from pydantic import BaseModel, EmailStr
from app.schemas.session import SessionResponse
from app.schemas.user import UserResponse
from app.schemas.enums import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    user: UserResponse
    token: TokenResponse
    session: SessionResponse


class UserSession(BaseModel):
    user_id: uuid.UUID
    email: EmailStr
    role: UserRole
    session_id: uuid.UUID
