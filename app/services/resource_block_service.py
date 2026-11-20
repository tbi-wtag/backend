import uuid
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.resource_block import crud_resource_block
from app.models.resource_block import ResourceBlock
from app.schemas.resource_block import ResourceBlockCreate
from app.services import resource_service
from app.services.audit_service import audit_service


async def create_resource_block(
    db: AsyncSession,
    *,
    block_in: ResourceBlockCreate,
    created_by: Optional[uuid.UUID] = None,
    request: Optional[Request] = None,
) -> ResourceBlock:
    resource = await resource_service.get_resource_by_id(
        db, resource_id=block_in.resource_id
    )

    overlapping = await crud_resource_block.get_overlapping_for_resource(
        db,
        resource_id=resource.id,
        start_at=block_in.start_at,
        end_at=block_in.end_at,
    )
    if overlapping:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This resource already has a maintenance block overlapping the requested time range.",
        )

    block_data = block_in.model_dump()
    block_data["created_by"] = created_by

    block = await crud_resource_block.create(db, obj_in=block_data, flush=True)

    await audit_service.log_event(
        db=db,
        action="RESOURCE_BLOCK_CREATE",
        request=request,
        status="SUCCESS",
        details={
            "block_id": str(block.id),
            "resource_id": str(block.resource_id),
            "start_at": block.start_at.isoformat(),
            "end_at": block.end_at.isoformat(),
            "reason": block.reason,
        },
        flush=True,
    )

    await db.commit()
    await db.refresh(block)
    return block


async def get_resource_blocks(
    db: AsyncSession,
    *,
    resource_id: Optional[uuid.UUID] = None,
    start_at: Optional[datetime] = None,
    end_at: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[ResourceBlock]:
    if resource_id is not None:
        await resource_service.get_resource_by_id(db, resource_id=resource_id)

    return await crud_resource_block.get_multi_filtered(
        db,
        resource_id=resource_id,
        start_at=start_at,
        end_at=end_at,
        skip=skip,
        limit=limit,
    )


async def delete_resource_block(
    db: AsyncSession,
    *,
    block_id: uuid.UUID,
    request: Optional[Request] = None,
) -> None:
    block = await crud_resource_block.get(db, id=block_id)
    if not block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance block not found.",
        )

    await crud_resource_block.remove(db, id=block_id, flush=True)

    await audit_service.log_event(
        db=db,
        action="RESOURCE_BLOCK_DELETE",
        request=request,
        status="SUCCESS",
        details={
            "block_id": str(block_id),
            "resource_id": str(block.resource_id),
        },
        flush=True,
    )

    await db.commit()
