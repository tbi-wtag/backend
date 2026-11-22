import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.booking import crud_booking
from app.models.booking import Booking
from app.models.payment import Payment
from app.schemas.auth import UserSession
from app.schemas.booking import AllocatedResourceItem, BookingResponse
from app.schemas.enums import UserRole


def generate_booking_reference(now_utc: datetime) -> str:
    return f"BK-{now_utc:%Y%m%d}-{secrets.token_hex(3).upper()}"


def to_booking_response(booking: Booking) -> BookingResponse:
    latest_payment = (
        max(booking.payments, key=lambda p: p.created_at) if booking.payments else None
    )
    if latest_payment is None and booking.series_id is not None:
        series_payments = (
            booking.booking_series.payments if booking.booking_series else []
        )
        latest_payment = (
            max(series_payments, key=lambda p: p.created_at)
            if series_payments
            else None
        )
    payment_status = latest_payment.status if latest_payment else "unpaid"

    resources = [
        AllocatedResourceItem.model_validate(br.resource)
        for br in booking.booking_resources
    ]

    return BookingResponse(
        id=booking.id,
        reference=booking.reference,
        user_id=booking.user_id,
        sport_id=booking.sport_id,
        series_id=booking.series_id,
        sport_name=booking.sport.sport_name,
        start_at=booking.start_at,
        end_at=booking.end_at,
        duration_minutes=booking.duration_minutes,
        number_of_people=booking.number_of_people,
        status=booking.status,
        payment_status=payment_status,
        total_price=booking.total_price,
        expired_at=booking.expired_at,
        cancelled_at=booking.cancelled_at,
        created_at=booking.created_at,
        allocated_resources=resources,
    )


def ensure_booking_access(booking: Booking, current_user: UserSession) -> None:
    if current_user.role != UserRole.ADMIN and booking.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this booking.",
        )


def apply_refund_if_eligible(booking: Booking, now_utc: datetime) -> bool:
    cutoff = timedelta(hours=settings.booking.cancellation_cutoff_hours)
    if booking.start_at - now_utc <= cutoff:
        return False

    paid_payment: Optional[Payment] = max(
        (
            payment
            for payment in booking.payments
            if payment.status in {"paid", "partially_refunded"}
        ),
        key=lambda payment: payment.created_at,
        default=None,
    )
    if not paid_payment:
        return False

    remaining_refundable = paid_payment.amount - paid_payment.refunded_amount
    refund_amount = min(booking.total_price, remaining_refundable)
    if refund_amount <= 0:
        return False

    paid_payment.refunded_amount += refund_amount
    paid_payment.refunded_at = now_utc
    paid_payment.status = (
        "refunded"
        if paid_payment.refunded_amount >= paid_payment.amount
        else "partially_refunded"
    )
    return True


async def sync_booking_statuses(db: AsyncSession) -> tuple[int, int]:
    now_utc = datetime.now(timezone.utc)
    expired_count = await crud_booking.expire_unpaid_bookings(db, now_utc=now_utc)
    completed_count = await crud_booking.complete_past_bookings(db, now_utc=now_utc)
    if expired_count or completed_count:
        await db.commit()
    return expired_count, completed_count
