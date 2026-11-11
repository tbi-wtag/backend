from typing import Optional
from fastapi import HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.schemas.user import UserCreate, UserPasswordUpdate
from app.models.user import User
from app.services.auth_service import logout_user
from app.services.audit_service import audit_service
from app.crud.user import crud_user


async def check_email_unique(db: AsyncSession, email: str) -> None:
    existing_user = await crud_user.get_by_email(db, email=email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists",
        )


async def check_username_unique(db: AsyncSession, username: str) -> None:
    existing_user = await crud_user.get_by_username(db, username=username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This username is already taken",
        )


async def register_user(db: AsyncSession, user_in: UserCreate, request: Optional[Request] = None):
    await check_email_unique(db, email=user_in.email)
    await check_username_unique(db, username=user_in.username)

    hashed_pwd = hash_password(user_in.password)

    new_user = await crud_user.create_user(db, user_in=user_in, hashed_password=hashed_pwd)

    await audit_service.log_event(
        db=db,
        action="USER_REGISTER",
        user_id=str(new_user.id),
        request=request,
        status="SUCCESS",
        details={"email": new_user.email, "username": new_user.username},
        flush=True,
    )

    await db.commit()
    await db.refresh(new_user)

    return new_user
    
async def update_user_profile(
    db: AsyncSession, current_user: User, update_data: dict, request: Optional[Request] = None
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

    
    updated_user = await crud_user.update_user_details(
        db=db,
        user=current_user,
        obj_in=update_data,
    )

    await audit_service.log_event(
        db=db,
        action="USER_UPDATE_PROFILE",
        user_id=str(updated_user.id),
        request=request,
        status="SUCCESS",
        details={"updated_fields": list(update_data.keys())},
        flush=True,
    )

    await db.commit()
    await db.refresh(updated_user)

    return updated_user

async def change_user_password(
    db: AsyncSession,
    user: User,
    data: UserPasswordUpdate,
    request: Optional[Request] = None
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

    await audit_service.log_event(
        db=db,
        action="USER_CHANGE_PASSWORD",
        user_id=str(user.id),
        request=request,
        status="SUCCESS",
        details={"revoked_sessions": True},
        flush=True,
    )

    await logout_user(db, user_id=user.id)
    
    await db.commit()
    await db.refresh(user)

    
