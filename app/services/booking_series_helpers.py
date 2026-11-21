import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import NoReturn, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.booking import crud_booking
from app.crud.resource import crud_resource
from app.crud.resource_block import crud_resource_block
from app.models.booking import Booking
from app.models.booking_series import BookingSeries
from app.models.payment import Payment
from app.models.resource import Resource
from app.schemas.auth import UserSession
from app.schemas.booking_series import (
    BookingSeriesResponse,
    SeriesClashDetail,
    SeriesPaymentSummary,
)
from app.schemas.enums import UserRole
from app.services import slot_service
from app.services.booking_helpers import to_booking_response


def raise_series_clashes(clashes: list[SeriesClashDetail]) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "message": "One or more weekly booking slots are unavailable.",
            "clashing_dates": [clash.model_dump(mode="json") for clash in clashes],
        },
    )


def generate_weekly_starts_in_month(first_start: datetime) -> list[datetime]:
    first_start_utc = (
        first_start.replace(tzinfo=timezone.utc)
        if first_start.tzinfo is None
        else first_start.astimezone(timezone.utc)
    )
    month = first_start_utc.month
    starts = []
    current_start = first_start_utc

    while current_start.month == month:
        starts.append(current_start)
        current_start += timedelta(days=7)

    return starts


async def resolve_and_lock_weeks(
    db: AsyncSession,
    *,
    starts: list[datetime],
    sport_id: uuid.UUID,
    duration_minutes: int,
    number_of_people: int,
    resource_ids: Optional[list[uuid.UUID]] = None,
    pitch_format: Optional[str] = None,
    surface: Optional[str] = None,
) -> tuple[list[tuple[datetime, datetime, list[Resource]]], datetime]:
    resolved: list[tuple[datetime, datetime, list[Resource]]] = []
    clashes: list[SeriesClashDetail] = []
    duration = timedelta(minutes=duration_minutes)

    for week_start in starts:
        try:
            allocated, slot_start, slot_end = (
                await slot_service.resolve_and_validate_resources(
                    db,
                    sport_id=sport_id,
                    start_at=week_start,
                    duration_minutes=duration_minutes,
                    number_of_people=number_of_people,
                    resource_ids=resource_ids,
                    pitch_format=pitch_format,
                    surface=surface,
                )
            )
        except HTTPException as exc:
            if exc.status_code != status.HTTP_409_CONFLICT:
                raise
            clashes.append(
                SeriesClashDetail(
                    date=week_start.date(),
                    start_at=week_start,
                    end_at=week_start + duration,
                    reason=str(exc.detail),
                )
            )
            continue
        resolved.append((slot_start, slot_end, allocated))

    if clashes:
        raise_series_clashes(clashes)

    all_ids = sorted(
        {resource.id for _, _, resources in resolved for resource in resources}, key=str
    )
    locked_by_id = {
        resource.id: resource
        for resource in await crud_resource.lock_active_by_ids(db, resource_ids=all_ids)
    }

    now_utc = datetime.now(timezone.utc)
    locked_clashes: list[SeriesClashDetail] = []
    locked_weeks: list[tuple[datetime, datetime, list[Resource]]] = []

    for slot_start, slot_end, resources in resolved:
        week_ids = [resource.id for resource in resources]
        inactive = any(resource_id not in locked_by_id for resource_id in week_ids)
        overlapping_bookings = await crud_booking.get_overlapping_booking_resources(
            db,
            resource_ids=week_ids,
            start_at=slot_start,
            end_at=slot_end,
            now_utc=now_utc,
        )
        overlapping_blocks = await crud_resource_block.get_overlapping_for_resources(
            db,
            resource_ids=week_ids,
            start_at=slot_start,
            end_at=slot_end,
        )

        if inactive or overlapping_bookings or overlapping_blocks:
            reason = (
                "One or more selected resources are no longer active."
                if inactive
                else "One or more selected resources are no longer available for this slot."
            )
            locked_clashes.append(
                SeriesClashDetail(
                    date=slot_start.date(),
                    start_at=slot_start,
                    end_at=slot_end,
                    reason=reason,
                )
            )
            continue

        locked_weeks.append(
            (
                slot_start,
                slot_end,
                [locked_by_id[resource_id] for resource_id in week_ids],
            )
        )

    if locked_clashes:
        raise_series_clashes(locked_clashes)

    return locked_weeks, now_utc


def ensure_series_access(series: BookingSeries, current_user: UserSession) -> None:
    if current_user.role != UserRole.ADMIN and series.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this booking series.",
        )


def apply_series_week_refund_if_eligible(
    series: BookingSeries, booking: Booking, now_utc: datetime
) -> bool:
    latest_payment = (
        max(series.payments, key=lambda payment: payment.created_at)
        if series.payments
        else None
    )
    if latest_payment is None or latest_payment.status not in {
        "paid",
        "partially_refunded",
    }:
        return False

    cutoff = timedelta(hours=settings.booking.cancellation_cutoff_hours)
    if booking.start_at - now_utc < cutoff:
        return False

    remaining_refundable = latest_payment.amount - latest_payment.refunded_amount
    if remaining_refundable <= Decimal("0.00"):
        return False

    refund_amount = min(booking.total_price, remaining_refundable)
    latest_payment.refunded_amount += refund_amount
    latest_payment.refunded_at = now_utc
    latest_payment.status = (
        "refunded"
        if latest_payment.refunded_amount >= latest_payment.amount
        else "partially_refunded"
    )
    return True


def to_series_response(series: BookingSeries) -> BookingSeriesResponse:
    latest_payment: Payment | None = (
        max(series.payments, key=lambda payment: payment.created_at)
        if series.payments
        else None
    )

    return BookingSeriesResponse(
        id=series.id,
        user_id=series.user_id,
        start_at=series.start_at,
        end_at=series.end_at,
        total_price=sum(
            (booking.total_price for booking in series.bookings), Decimal("0.00")
        ),
        payment=(
            SeriesPaymentSummary.model_validate(latest_payment)
            if latest_payment
            else None
        ),
        created_at=series.created_at,
        bookings=[
            to_booking_response(booking)
            for booking in sorted(series.bookings, key=lambda item: item.start_at)
        ],
    )
