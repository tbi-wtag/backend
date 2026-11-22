import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.booking_series import crud_booking_series
from app.models.booking import Booking
from app.models.booking_resource import BookingResource
from app.models.booking_series import BookingSeries
from app.models.payment import Payment
from app.schemas.auth import UserSession
from app.schemas.booking_series import (
    BookingSeriesResponse,
    MonthlyBookingCreate,
)
from app.schemas.enums import UserRole
from app.services import pricing_service
from app.services.audit_service import audit_service
from app.services.booking_helpers import generate_booking_reference
from app.services.booking_series_helpers import (
    apply_series_week_refund_if_eligible,
    ensure_series_access,
    generate_weekly_starts_in_month,
    resolve_and_lock_weeks,
    to_series_response,
)


async def create_monthly_booking(
    db: AsyncSession,
    *,
    series_in: MonthlyBookingCreate,
    current_user: UserSession,
) -> BookingSeriesResponse:
    starts = generate_weekly_starts_in_month(series_in.start_at)
    if len(starts) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A monthly booking series must include at least two weeks.",
        )

    locked_weeks, now_utc = await resolve_and_lock_weeks(
        db,
        starts=starts,
        sport_id=series_in.sport_id,
        duration_minutes=series_in.duration_minutes,
        number_of_people=series_in.number_of_people,
        resource_ids=series_in.resource_ids,
        pitch_format=series_in.pitch_format,
        surface=series_in.surface,
    )

    expired_at = now_utc + timedelta(
        minutes=settings.booking.pending_payment_hold_minutes
    )
    series = BookingSeries(
        user_id=current_user.user_id,
        start_at=locked_weeks[0][0].date(),
        end_at=locked_weeks[-1][0].date(),
    )
    db.add(series)
    await db.flush()

    total_series_price = Decimal("0.00")
    for slot_start, slot_end, resources in locked_weeks:
        week_price = pricing_service.calculate_total_price(
            resources, series_in.duration_minutes
        )
        total_series_price += week_price
        booking = Booking(
            reference=generate_booking_reference(now_utc),
            user_id=current_user.user_id,
            sport_id=series_in.sport_id,
            series_id=series.id,
            start_at=slot_start,
            end_at=slot_end,
            duration_minutes=series_in.duration_minutes,
            number_of_people=series_in.number_of_people,
            status="pending",
            total_price=week_price,
            expired_at=expired_at,
            booking_resources=[
                BookingResource(
                    resource_id=resource.id,
                    start_at=slot_start,
                    end_at=slot_end,
                    is_active=True,
                )
                for resource in resources
            ],
        )
        db.add(booking)

    db.add(
        Payment(
            user_id=current_user.user_id,
            series_id=series.id,
            booking_id=None,
            amount=total_series_price,
            status="pending",
        )
    )
    await db.commit()

    created = await crud_booking_series.get_with_details(db, series_id=series.id)
    assert created is not None
    return to_series_response(created)


async def list_booking_series(
    db: AsyncSession,
    *,
    current_user: UserSession,
    user_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[BookingSeriesResponse]:
    target_user_id = (
        user_id if current_user.role == UserRole.ADMIN else current_user.user_id
    )
    series_list = await crud_booking_series.get_multi_filtered(
        db, user_id=target_user_id, skip=skip, limit=limit
    )
    return [to_series_response(series) for series in series_list]


async def get_booking_series_by_id(
    db: AsyncSession, *, series_id: uuid.UUID, current_user: UserSession
) -> BookingSeriesResponse:
    series = await _get_owned_series(db, series_id=series_id, current_user=current_user)
    return to_series_response(series)


async def _get_owned_series(
    db: AsyncSession, *, series_id: uuid.UUID, current_user: UserSession
) -> BookingSeries:
    series = await crud_booking_series.get_with_details(db, series_id=series_id)
    if series is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking series not found.",
        )
    ensure_series_access(series, current_user)
    return series


async def _cancel_series_weeks(
    db: AsyncSession,
    *,
    series: BookingSeries,
    bookings: list[Booking],
    current_user: UserSession,
    request: Optional[Request],
    now_utc: datetime,
    action: str,
) -> BookingSeriesResponse:
    if not bookings:
        return to_series_response(series)

    was_paid = any(
        payment.status in {"paid", "partially_refunded", "refunded"}
        for payment in series.payments
    )
    refund_initiated: list[uuid.UUID] = []
    for booking in bookings:
        booking.status = "cancelled"
        booking.cancelled_at = now_utc
        for booking_resource in booking.booking_resources:
            booking_resource.is_active = False
        if apply_series_week_refund_if_eligible(series, booking, now_utc):
            refund_initiated.append(booking.id)

    if series.bookings and all(
        booking.status == "cancelled" for booking in series.bookings
    ):
        for payment in series.payments:
            if payment.status == "pending":
                payment.status = "cancelled"

    if was_paid:
        await audit_service.log_event(
            db=db,
            action=action,
            user_id=str(current_user.user_id),
            request=request,
            status="SUCCESS",
            details={
                "series_id": str(series.id),
                "booking_ids": [str(booking.id) for booking in bookings],
                "refund_initiated_booking_ids": [
                    str(booking_id) for booking_id in refund_initiated
                ],
            },
            flush=True,
        )

    await db.commit()
    updated = await crud_booking_series.get_with_details(db, series_id=series.id)
    assert updated is not None
    return to_series_response(updated)


async def cancel_series_week(
    db: AsyncSession,
    *,
    series_id: uuid.UUID,
    booking_id: uuid.UUID,
    current_user: UserSession,
    request: Optional[Request] = None,
) -> BookingSeriesResponse:
    series = await _get_owned_series(db, series_id=series_id, current_user=current_user)
    booking = next((item for item in series.bookings if item.id == booking_id), None)
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking week not found in this series.",
        )
    if booking.status not in {"pending", "confirmed"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel a booking with status '{booking.status}'.",
        )

    now_utc = datetime.now(timezone.utc)
    if booking.start_at <= now_utc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a booking that has already started or passed.",
        )

    return await _cancel_series_weeks(
        db,
        series=series,
        bookings=[booking],
        current_user=current_user,
        request=request,
        now_utc=now_utc,
        action="BOOKING_SERIES_WEEK_CANCEL",
    )


async def cancel_upcoming_series_weeks(
    db: AsyncSession,
    *,
    series_id: uuid.UUID,
    current_user: UserSession,
    request: Optional[Request] = None,
) -> BookingSeriesResponse:
    series = await _get_owned_series(db, series_id=series_id, current_user=current_user)
    now_utc = datetime.now(timezone.utc)
    upcoming = [
        booking
        for booking in series.bookings
        if booking.status in {"pending", "confirmed"} and booking.start_at > now_utc
    ]
    return await _cancel_series_weeks(
        db,
        series=series,
        bookings=upcoming,
        current_user=current_user,
        request=request,
        now_utc=now_utc,
        action="BOOKING_SERIES_CANCEL_UPCOMING",
    )
