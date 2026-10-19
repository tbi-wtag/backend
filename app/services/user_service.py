from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate

async def get_user_by_email(db: AsyncSession, email:str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def get_user_by_username(db:AsyncSession, username:str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()

async def register_user(db: AsyncSession, user_in: UserCreate):
    if await get_user_by_email(db, email=user_in.email):
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "A user with this email address already exists",
        )   

    if await get_user_by_username(db, username=user_in.username):
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "This username is already taken",
        )

    hashed_pwd = hash_password(user_in.password)

    new_user = User(
        username = user_in.username,
        email = user_in.email,
        first_name = user_in.first_name,
        last_name = user_in.last_name,
        hashed_password = hashed_pwd,
        role = "user",
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user
