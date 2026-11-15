import uuid
from typing import Any, Dict, Optional, Union
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.enums import UserRole
from app.crud.base import CRUDBase
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):

    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        result = await db.execute(select(self.model).where(self.model.email == email))
        return result.scalars().first()

    async def get_by_username(
        self, db: AsyncSession, *, username: str
    ) -> Optional[User]:
        result = await db.execute(
            select(self.model).where(self.model.username == username)
        )
        return result.scalars().first()

    async def create_user(
        self,
        db: AsyncSession,
        *,
        user_in: UserCreate,
        hashed_password: str,
        role: UserRole = UserRole.USER,
        flush: bool = False,
    ) -> User:
        user_data = user_in.model_dump(exclude={"password", "confirm_password"})
        user_data["hashed_password"] = hashed_password
        user_data["role"] = role.value

        return await self.create(db, obj_in=user_data, flush=flush)

    async def update_user_details(
        self,
        db: AsyncSession,
        *,
        user: User,
        obj_in: Union[UserUpdate, Dict[str, Any]],
        flush: bool = False,
    ) -> User:
        update_data = (
            obj_in.copy()
            if isinstance(obj_in, dict)
            else obj_in.model_dump(exclude_unset=True)
        )

        disallowed_fields = {
            "id",
            "hashed_password",
            "role",
            "is_active",
            "created_at",
            "updated_at",
        }
        for field in disallowed_fields:
            update_data.pop(field, None)

        return await self.update(db, db_obj=user, obj_in=update_data, flush=flush)


crud_user = CRUDUser(User)
