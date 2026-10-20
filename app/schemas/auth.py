from pydantic import BaseModel
from app.schemas.session import SessionResponse
from app.schemas.user import UserResponse

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginResponse(BaseModel):
    user: UserResponse
    token: TokenResponse
    session: SessionResponse

