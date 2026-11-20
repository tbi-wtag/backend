import uuid
from datetime import datetime
from typing import Any, Optional
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_db
from app.core.rate_limiter import limiter
from app.models.resource_block import ResourceBlock
from app.schemas.resource_block import ResourceBlockCreate, ResourceBlockResponse
from app.services import resource_block_service

router = APIRouter(prefix="/time-blocks", tags=["Admin - Time Blocks"])


@router.post(
    "",
    response_model=ResourceBlockResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("20/minute")
async def create_time_block(
    request: Request,
    response: Response,
    block_in: ResourceBlockCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> ResourceBlock:
    return await resource_block_service.create_resource_block(
        db=db,
        block_in=block_in,
        created_by=current_user.user_id,
        request=request,
    )


@router.get("", response_model=list[ResourceBlockResponse])
async def list_time_blocks(
    resource_id: Optional[uuid.UUID] = None,
    start_at: Optional[datetime] = None,
    end_at: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> list[ResourceBlock]:
    return await resource_block_service.get_resource_blocks(
        db=db,
        resource_id=resource_id,
        start_at=start_at,
        end_at=end_at,
        skip=skip,
        limit=limit,
    )


@router.delete("/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def delete_time_block(
    request: Request,
    response: Response,
    block_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    await resource_block_service.delete_resource_block(
        db=db, block_id=block_id, request=request
    )
