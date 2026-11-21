import uuid
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_db
from app.core.rate_limiter import limiter
from app.models.resource import Resource
from app.schemas.resource import ResourceCreate, ResourceResponse, ResourceUpdate
from app.services import resource_service

router = APIRouter(prefix="/resources", tags=["Admin - Resources"])


@router.post(
    "",
    response_model=ResourceResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
async def create_resource(
    request: Request,
    response: Response,
    resource_in: ResourceCreate,
    db: AsyncSession = Depends(get_db),
) -> Resource:
    return await resource_service.create_resource(
        db=db, resource_in=resource_in, request=request
    )


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Resource:
    return await resource_service.get_resource_by_id(db=db, resource_id=resource_id)


@router.patch("/{resource_id}", response_model=ResourceResponse)
@limiter.limit("20/minute")
async def update_resource(
    request: Request,
    response: Response,
    resource_id: uuid.UUID,
    resource_in: ResourceUpdate,
    db: AsyncSession = Depends(get_db),
) -> Resource:
    return await resource_service.update_resource(
        db=db, resource_id=resource_id, resource_in=resource_in, request=request
    )


@router.delete("/{resource_id}", response_model=ResourceResponse)
@limiter.limit("10/minute")
async def deactivate_resource(
    request: Request,
    response: Response,
    resource_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Resource:
    return await resource_service.deactivate_resource(
        db=db, resource_id=resource_id, request=request
    )
