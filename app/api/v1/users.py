import uuid
from typing import Any, Dict
from app.schemas.user import UserUpdate, UserResponse
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.auth.dependencies import get_current_user_from_db

from app.db.session import get_db
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user_from_db),
) -> User:
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_user_profile(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user_from_db),
    db: AsyncSession = Depends(get_db),
):
    update_data = user_in.model_dump(exclude_unset=True)
    return await user_service.update_user_profile(
        db=db,
        current_user=current_user,
        update_data=update_data,
    )
