import uuid
from decimal import Decimal
from typing import Optional
from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.resource import crud_resource
from app.models.resource import Resource
from app.schemas.resource import ResourceCreate, ResourceUpdate
from app.services import sport_service
from app.services.audit_service import audit_service

from app.services.resource_validators import (
    ensure_under_resource_limit,
    ensure_unique_name,
    validate_sport_specific_rules,
)


async def create_resource(
    db: AsyncSession,
    *,
    resource_in: ResourceCreate,
    request: Optional[Request] = None,
) -> Resource:
    sport = await sport_service.get_sport_by_id(db, sport_id=resource_in.sport_id)
    validate_sport_specific_rules(
        sport_name=sport.sport_name,
        pitch_format=resource_in.pitch_format,
        surface=resource_in.surface,
        capacity=resource_in.capacity,
    )
    if resource_in.is_active:
        await ensure_under_resource_limit(db, sport)
    await ensure_unique_name(db, sport, resource_in.resource_name)

    resource = await crud_resource.create(db, obj_in=resource_in, flush=True)

    await audit_service.log_event(
        db=db,
        action="RESOURCE_CREATE",
        request=request,
        status="SUCCESS",
        details={
            "resource_id": str(resource.id),
            "sport_id": str(resource.sport_id),
            "resource_name": resource.resource_name,
        },
        flush=True,
    )

    await db.commit()
    await db.refresh(resource)
    return resource


async def get_resource_by_id(db: AsyncSession, *, resource_id: uuid.UUID) -> Resource:
    resource = await crud_resource.get(db, id=resource_id)
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found.",
        )
    return resource


async def get_resources_by_sport(
    db: AsyncSession,
    *,
    sport_id: uuid.UUID,
    is_active: Optional[bool] = True,
    pitch_format: Optional[str] = None,
    surface: Optional[str] = None,
    min_capacity: Optional[int] = None,
    max_price: Optional[Decimal] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Resource]:
    await sport_service.get_sport_by_id(db, sport_id=sport_id)
    return await crud_resource.get_by_sport_filtered(
        db,
        sport_id=sport_id,
        is_active=is_active,
        pitch_format=pitch_format,
        surface=surface,
        min_capacity=min_capacity,
        max_price=max_price,
        skip=skip,
        limit=limit,
    )


async def update_resource(
    db: AsyncSession,
    *,
    resource_id: uuid.UUID,
    resource_in: ResourceUpdate,
    request: Optional[Request] = None,
) -> Resource:
    resource = await get_resource_by_id(db, resource_id=resource_id)
    sport = await sport_service.get_sport_by_id(db, sport_id=resource.sport_id)

    updates = resource_in.model_dump(exclude_unset=True)
    validate_sport_specific_rules(
        sport_name=sport.sport_name,
        pitch_format=updates.get("pitch_format", resource.pitch_format),
        surface=updates.get("surface", resource.surface),
        capacity=updates.get("capacity", resource.capacity),
    )

    if not resource.is_active and updates.get("is_active") is True:
        await ensure_under_resource_limit(db, sport)

    new_name = updates.get("resource_name")
    if new_name and new_name.strip().lower() != resource.resource_name.lower():
        await ensure_unique_name(db, sport, new_name)

    was_active = resource.is_active
    updated = await crud_resource.update(
        db, db_obj=resource, obj_in=resource_in, flush=True
    )

    await audit_service.log_event(
        db=db,
        action=(
            "RESOURCE_DEACTIVATE"
            if was_active and not updated.is_active
            else "RESOURCE_UPDATE"
        ),
        request=request,
        status="SUCCESS",
        details={
            "resource_id": str(updated.id),
            "updated_fields": resource_in.model_dump(exclude_unset=True, mode="json"),
        },
        flush=True,
    )

    await db.commit()
    await db.refresh(updated)
    return updated


async def deactivate_resource(
    db: AsyncSession,
    *,
    resource_id: uuid.UUID,
    request: Optional[Request] = None,
) -> Resource:
    resource = await get_resource_by_id(db, resource_id=resource_id)
    if not resource.is_active:
        return resource
    return await update_resource(
        db,
        resource_id=resource_id,
        resource_in=ResourceUpdate(is_active=False),
        request=request,
    )
