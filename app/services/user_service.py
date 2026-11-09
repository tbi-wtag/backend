from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.schemas.user import UserCreate, UserPasswordUpdate
from app.crud import user
from app.models.user import User
from app.services.auth_service import logout_user


async def check_email_unique(db: AsyncSession, email: str) -> None:
    existing_user = await user.get_user_by_email(db, email=email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists",
        )


async def check_username_unique(db: AsyncSession, username: str) -> None:
    existing_user = await user.get_user_by_username(db, username=username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This username is already taken",
        )


async def register_user(db: AsyncSession, user_in: UserCreate):
    await check_email_unique(db, email=user_in.email)
    await check_username_unique(db, username=user_in.username)

    hashed_pwd = hash_password(user_in.password)

    return await user.create_user(db, user_in=user_in, hashed_password=hashed_pwd)


async def update_user_profile(
    db: AsyncSession, current_user: User, update_data: dict
) -> User:
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided for update",
        )

    if "email" in update_data and update_data["email"] != current_user.email:
        await check_email_unique(db, email=update_data["email"])

    if "username" in update_data and update_data["username"] != current_user.username:
        await check_username_unique(db, username=update_data["username"])

    return await user.update_user_details(
        db=db,
        user=current_user,
        update_data=update_data,
    )


async def change_user_password(
    db: AsyncSession,
    user: User,
    data: UserPasswordUpdate,
) -> None:

    if not verify_password(data.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect old password"
        )

    if data.old_password == data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the old password",
        )

    user.hashed_password = hash_password(data.new_password)
    await db.commit()
    await db.refresh(user)

    await logout_user(db, user_id=user.id)
