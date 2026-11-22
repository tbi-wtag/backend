import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_db
from app.schemas.auth import UserSession
from app.schemas.payment import PaymentResponse
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["Payments"])
admin_router = APIRouter(prefix="/payments")


@router.get("/my", response_model=list[PaymentResponse])
async def get_my_payments(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: UserSession = Depends(get_current_user),
) -> list[PaymentResponse]:
    return await payment_service.list_payments(
        db=db,
        current_user=current_user,
        user_id=current_user.user_id,
        status_filter=status_filter,
        skip=skip,
        limit=limit,
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserSession = Depends(get_current_user),
) -> PaymentResponse:
    return await payment_service.get_payment_by_id(
        db=db,
        payment_id=payment_id,
        current_user=current_user,
    )


@admin_router.get("", response_model=list[PaymentResponse])
async def get_all_payments(
    user_id: Optional[uuid.UUID] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: UserSession = Depends(get_current_user),
) -> list[PaymentResponse]:
    return await payment_service.list_payments(
        db=db,
        current_user=current_user,
        user_id=user_id,
        status_filter=status_filter,
        skip=skip,
        limit=limit,
    )
