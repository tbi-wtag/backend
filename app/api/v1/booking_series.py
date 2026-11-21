import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_db
from app.core.rate_limiter import limiter
from app.schemas.auth import UserSession
from app.schemas.booking_series import BookingSeriesResponse, MonthlyBookingCreate
from app.services import booking_series_service

router = APIRouter(prefix="/booking-series", tags=["Booking Series"])
admin_router = APIRouter(prefix="/booking-series")


@router.post(
    "", response_model=BookingSeriesResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("10/minute")
async def create_monthly_booking_series(
    request: Request,
    response: Response,
    series_in: MonthlyBookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserSession = Depends(get_current_user),
) -> BookingSeriesResponse:
    return await booking_series_service.create_monthly_booking(
        db=db,
        series_in=series_in,
        current_user=current_user,
    )


@router.get("/my", response_model=list[BookingSeriesResponse])
async def get_my_booking_series(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: UserSession = Depends(get_current_user),
) -> list[BookingSeriesResponse]:
    return await booking_series_service.list_booking_series(
        db=db,
        current_user=current_user,
        user_id=current_user.user_id,
        skip=skip,
        limit=limit,
    )


@router.get("/{series_id}", response_model=BookingSeriesResponse)
async def get_booking_series(
    series_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserSession = Depends(get_current_user),
) -> BookingSeriesResponse:
    return await booking_series_service.get_booking_series_by_id(
        db=db,
        series_id=series_id,
        current_user=current_user,
    )


@router.post("/{series_id}/cancel", response_model=BookingSeriesResponse)
@limiter.limit("10/minute")
async def cancel_booking_series(
    series_id: uuid.UUID,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: UserSession = Depends(get_current_user),
) -> BookingSeriesResponse:
    return await booking_series_service.cancel_upcoming_series_weeks(
        db=db,
        series_id=series_id,
        current_user=current_user,
        request=request,
    )


@router.post(
    "/{series_id}/bookings/{booking_id}/cancel",
    response_model=BookingSeriesResponse,
)
@limiter.limit("10/minute")
async def cancel_booking_series_week(
    series_id: uuid.UUID,
    booking_id: uuid.UUID,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: UserSession = Depends(get_current_user),
) -> BookingSeriesResponse:
    return await booking_series_service.cancel_series_week(
        db=db,
        series_id=series_id,
        booking_id=booking_id,
        current_user=current_user,
        request=request,
    )


@admin_router.get("", response_model=list[BookingSeriesResponse])
async def get_all_booking_series(
    user_id: Optional[uuid.UUID] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: UserSession = Depends(get_current_user),
) -> list[BookingSeriesResponse]:
    return await booking_series_service.list_booking_series(
        db=db,
        current_user=current_user,
        user_id=user_id,
        skip=skip,
        limit=limit,
    )
