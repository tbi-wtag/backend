from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from app.api.dependencies import get_db
from app.models.user import User
from app.models.session import Session as SessionModel
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import login_user
from app.services.user_service import register_user
from app.api.dependencies import get_current_user
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post(
    "/register",
    response_model = UserResponse,
    status_code = status.HTTP_201_CREATED,
)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    return await register_user(db = db, user_in = user_in)

@router.post(
    "/login",
    response_model = LoginResponse,
    status_code = status.HTTP_200_OK,
)
async def login(credentials: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    login_data = await login_user(db = db, credentials = credentials)

    response.set_cookie(
        key = "access_token",
        value = login_data.token.access_token,
        httponly = True,
        secure = False ,
        samesite = "lax",
        max_age = 10080 * 60,
    )

    return login_data

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user

@router.get("/logout",status_code = status.HTTP_200_OK)
async def logout(response: Response, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await auth_service.logout_user(db, user_id = current_user.id)

    response.delete_cookie(key = "access_token")

    return {"message": "Successfully logged out"}