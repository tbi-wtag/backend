from typing import Optional, Sequence
import uuid
from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.sport import crud_sport
from app.models.sport import Sport
from app.schemas.sport import SportCreate, SportUpdate
from app.services.audit_service import audit_service


async def create_sport(
    db: AsyncSession, *, sport_in: SportCreate, request: Optional[Request] = None
) -> Sport:

    existing = await crud_sport.get_by_name(db, sport_name=sport_in.sport_name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sport '{sport_in.sport_name}' already exists.",
        )

    new_sport = await crud_sport.create(db, obj_in=sport_in, flush=True)

    await audit_service.log_event(
        db=db,
        action="SPORT_CREATE",
        request=request,
        status="SUCCESS",
        details={"sport_id": str(new_sport.id), "sport_name": new_sport.sport_name},
        flush=True,
    )

    await db.commit()
    await db.refresh(new_sport)
    return new_sport


async def get_sports(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> Sequence[Sport]:
    return await crud_sport.get_multi(db, skip=skip, limit=limit)


async def get_sport_by_id(db: AsyncSession, sport_id: uuid.UUID) -> Sport:
    sport = await crud_sport.get(db, id=sport_id)
    if not sport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sport not found.",
        )
    return sport


async def update_sport(
    db: AsyncSession,
    *,
    sport_id: uuid.UUID,
    sport_in: SportUpdate,
    request: Optional[Request] = None,
) -> Sport:
    sport = await get_sport_by_id(db, sport_id=sport_id)

    if (
        sport_in.sport_name
        and sport_in.sport_name.strip().lower() != sport.sport_name.lower()
    ):
        existing = await crud_sport.get_by_name(db, sport_name=sport_in.sport_name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sport '{sport_in.sport_name}' already exists.",
            )

    new_min = sport_in.min_hours if sport_in.min_hours is not None else sport.min_hours
    new_max = sport_in.max_hours if sport_in.max_hours is not None else sport.max_hours
    if new_min is not None and new_max is not None and new_max < new_min:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="max_hours must be greater than or equal to min_hours.",
        )

    updated_sport = await crud_sport.update(
        db, db_obj=sport, obj_in=sport_in, flush=True
    )

    await audit_service.log_event(
        db=db,
        action="SPORT_UPDATE",
        request=request,
        status="SUCCESS",
        details={
            "sport_id": str(updated_sport.id),
            "updated_fields": sport_in.model_dump(exclude_unset=True),
        },
        flush=True,
    )

    await db.commit()
    await db.refresh(updated_sport)
    return updated_sport


async def delete_sport(
    db: AsyncSession,
    *,
    sport_id: uuid.UUID,
    request: Optional[Request] = None,
) -> None:
    sport = await get_sport_by_id(db, sport_id=sport_id)
    sport_name = sport.sport_name

    await crud_sport.remove(db, id=sport_id, flush=True)

    await audit_service.log_event(
        db=db,
        action="SPORT_DELETE",
        request=request,
        status="SUCCESS",
        details={"sport_id": str(sport_id), "sport_name": sport_name},
        flush=True,
    )

    await db.commit()
