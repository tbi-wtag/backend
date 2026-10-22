from pydantic import BaseModel
from app.schemas.session import SessionResponse
from app.schemas.user import UserResponse
from pydantic import EmailStr

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

