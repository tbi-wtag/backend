from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
import uuid
from pydantic import BaseModel
from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: uuid.UUID | str) -> Optional[ModelType]:
        result = await db.execute(
            select(self.model).where(getattr(self.model, "id") == id)
        )
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        order_col = getattr(self.model, "created_at", getattr(self.model, "id", None))

        query = select(self.model)
        if order_col is not None:
            query = query.order_by(desc(order_col))

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: Union[CreateSchemaType, Dict[str, Any]],
        flush: bool = False,
    ) -> ModelType:
        if isinstance(obj_in, dict):
            create_data = obj_in
        else:
            create_data = obj_in.model_dump()

        db_obj = self.model(**create_data)
        db.add(db_obj)

        if flush:
            await db.flush()
        else:
            await db.commit()

        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        flush: bool = False,
    ) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)

        if flush:
            await db.flush()
        else:
            await db.commit()

        await db.refresh(db_obj)
        return db_obj

    async def remove(
        self,
        db: AsyncSession,
        *,
        id: uuid.UUID | str,
        flush: bool = False,
    ) -> Optional[ModelType]:
        obj = await self.get(db, id=id)
        if obj:
            await db.delete(obj)
            if flush:
                await db.flush()
            else:
                await db.commit()
        return obj
