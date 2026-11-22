import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_db
from app.core.rate_limiter import limiter
from app.schemas.auth import UserSession
from app.schemas.booking import BookingCreate, BookingResponse
from app.schemas.payment import PaymentProcessRequest, PaymentResponse
from app.services import booking_service
from app.services import payment_service

router = APIRouter(prefix="/bookings", tags=["Bookings"])
admin_router = APIRouter(prefix="/bookings")


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_booking(
    request: Request,
    response: Response,
    booking_in: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserSession = Depends(get_current_user),
) -> BookingResponse:
    return await booking_service.create_booking(
        db=db,
        booking_in=booking_in,
        current_user=current_user,
    )


@router.get("/my", response_model=list[BookingResponse])
async def get_my_bookings(
    sport_id: Optional[uuid.UUID] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    start_from: Optional[datetime] = Query(default=None),
    start_to: Optional[datetime] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: UserSession = Depends(get_current_user),
) -> list[BookingResponse]:
    return await booking_service.list_bookings(
        db=db,
        current_user=current_user,
        sport_id=sport_id,
        status_filter=status_filter,
        start_from=start_from,
        start_to=start_to,
        user_id=current_user.user_id,
        skip=skip,
        limit=limit,
    )


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserSession = Depends(get_current_user),
) -> BookingResponse:
    return await booking_service.get_booking_by_id(
        db=db, booking_id=booking_id, current_user=current_user
    )


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
@limiter.limit("10/minute")
async def cancel_booking(
    booking_id: uuid.UUID,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: UserSession = Depends(get_current_user),
) -> BookingResponse:
    return await booking_service.cancel_booking(
        db=db,
        booking_id=booking_id,
        current_user=current_user,
        request=request,
    )


@router.post("/{booking_id}/payment", response_model=PaymentResponse)
@limiter.limit("10/minute")
async def pay_for_booking(
    booking_id: uuid.UUID,
    payment_in: PaymentProcessRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: UserSession = Depends(get_current_user),
) -> PaymentResponse:
    return await payment_service.pay_for_booking(
        db=db,
        booking_id=booking_id,
        payment_in=payment_in,
        current_user=current_user,
        request=request,
    )


@admin_router.get("", response_model=list[BookingResponse])
async def get_all_bookings(
    sport_id: Optional[uuid.UUID] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    start_from: Optional[datetime] = Query(default=None),
    start_to: Optional[datetime] = Query(default=None),
    user_id: Optional[uuid.UUID] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: UserSession = Depends(get_current_user),
) -> list[BookingResponse]:
    return await booking_service.list_bookings(
        db=db,
        current_user=current_user,
        sport_id=sport_id,
        status_filter=status_filter,
        start_from=start_from,
        start_to=start_to,
        user_id=user_id,
        skip=skip,
        limit=limit,
    )
