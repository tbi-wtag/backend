from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.schemas.user import UserCreate
from app.crud import user


async def register_user(db: AsyncSession, user_in: UserCreate):
    if await user.get_user_by_email(db, email=user_in.email):
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "A user with this email address already exists",
        )   

    if await user.get_user_by_username(db, username=user_in.username):
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "This username is already taken",
        )

    hashed_pwd = hash_password(user_in.password)

    return await user.create_user(db, user_in = user_in, hashed_password = hashed_pwd)
