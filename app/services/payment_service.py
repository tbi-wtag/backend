import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.booking import crud_booking
from app.crud.booking_series import crud_booking_series
from app.crud.payment import crud_payment
from app.models.payment import Payment
from app.schemas.auth import UserSession
from app.schemas.enums import UserRole
from app.schemas.payment import PaymentProcessRequest, PaymentResponse
from app.services.audit_service import audit_service
from app.services.booking_helpers import ensure_booking_access
from app.services.booking_series_helpers import ensure_series_access
from app.services.payment_gateway import get_payment_gateway


def _get_or_create_pending_payment(
    db: AsyncSession,
    *,
    payment: Optional[Payment],
    user_id: uuid.UUID,
    amount: Decimal,
    booking_id: Optional[uuid.UUID] = None,
    series_id: Optional[uuid.UUID] = None,
) -> Payment:
    if payment is None:
        payment = Payment(
            user_id=user_id,
            booking_id=booking_id,
            series_id=series_id,
            amount=amount,
            status="pending",
        )
        db.add(payment)
    elif payment.status == "failed":
        payment.status = "pending"
        payment.paid_at = None
    elif payment.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This payment cannot be processed in its current state.",
        )

    payment.amount = amount
    return payment


async def _finish_payment(
    db: AsyncSession,
    *,
    payment: Payment,
    result_success: bool,
    failure_reason: Optional[str],
    now_utc: datetime,
    reference_type: str,
    reference_id: uuid.UUID,
    current_user: UserSession,
    request: Optional[Request],
    transaction_reference: Optional[str],
) -> PaymentResponse:
    if not result_success:
        payment.status = "failed"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=failure_reason or "Payment was declined.",
        )

    payment.status = "paid"
    payment.paid_at = now_utc
    payment_id = payment.id
    await audit_service.log_event(
        db=db,
        action=f"{reference_type.upper()}_PAYMENT",
        user_id=str(current_user.user_id),
        request=request,
        status="SUCCESS",
        details={
            f"{reference_type}_id": str(reference_id),
            "payment_id": str(payment.id),
            "amount": str(payment.amount),
            "transaction_reference": transaction_reference,
        },
        flush=True,
    )
    await db.commit()

    paid_payment = await crud_payment.get_with_details(db, payment_id=payment_id)
    return PaymentResponse.model_validate(paid_payment)


async def pay_for_booking(
    db: AsyncSession,
    *,
    booking_id: uuid.UUID,
    payment_in: PaymentProcessRequest,
    current_user: UserSession,
    request: Optional[Request] = None,
) -> PaymentResponse:
    booking = await crud_booking.get_with_details(db, booking_id=booking_id)
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found.",
        )
    ensure_booking_access(booking, current_user)

    now_utc = datetime.now(timezone.utc)
    if booking.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending bookings can be paid.",
        )
    if booking.expired_at is not None and booking.expired_at <= now_utc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking payment window has expired.",
        )

    payment = await crud_payment.get_latest_by_booking_id(db, booking_id=booking.id)
    payment = _get_or_create_pending_payment(
        db,
        payment=payment,
        user_id=booking.user_id,
        booking_id=booking.id,
        amount=booking.total_price,
    )
    await db.flush()

    result = await get_payment_gateway().charge(
        amount=payment.amount,
        card_number=payment_in.card_number,
        reference=booking.reference,
    )
    if result.success:
        booking.status = "confirmed"
        booking.expired_at = None

    return await _finish_payment(
        db,
        payment=payment,
        result_success=result.success,
        failure_reason=result.failure_reason,
        now_utc=now_utc,
        reference_type="booking",
        reference_id=booking.id,
        current_user=current_user,
        request=request,
        transaction_reference=result.transaction_reference,
    )


async def pay_for_series(
    db: AsyncSession,
    *,
    series_id: uuid.UUID,
    payment_in: PaymentProcessRequest,
    current_user: UserSession,
    request: Optional[Request] = None,
) -> PaymentResponse:
    series = await crud_booking_series.get_with_details(db, series_id=series_id)
    if series is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking series not found.",
        )
    ensure_series_access(series, current_user)

    now_utc = datetime.now(timezone.utc)
    active_bookings = [b for b in series.bookings if b.status != "cancelled"]
    if not active_bookings or any(
        booking.status != "pending"
        or (booking.expired_at is not None and booking.expired_at <= now_utc)
        for booking in active_bookings
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All bookings in the series must be pending and unexpired.",
        )

    payment = await crud_payment.get_latest_by_series_id(db, series_id=series.id)
    total_price = sum(
        (booking.total_price for booking in active_bookings), Decimal("0.00")
    )
    payment = _get_or_create_pending_payment(
        db,
        payment=payment,
        user_id=series.user_id,
        series_id=series.id,
        amount=total_price,
    )
    await db.flush()

    result = await get_payment_gateway().charge(
        amount=payment.amount,
        card_number=payment_in.card_number,
        reference=f"BS-{series.id}",
    )
    if result.success:
        for booking in active_bookings:
            booking.status = "confirmed"
            booking.expired_at = None

    return await _finish_payment(
        db,
        payment=payment,
        result_success=result.success,
        failure_reason=result.failure_reason,
        now_utc=now_utc,
        reference_type="booking_series",
        reference_id=series.id,
        current_user=current_user,
        request=request,
        transaction_reference=result.transaction_reference,
    )


async def list_payments(
    db: AsyncSession,
    *,
    current_user: UserSession,
    user_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[PaymentResponse]:
    target_user_id = (
        user_id if current_user.role == UserRole.ADMIN else current_user.user_id
    )
    payments = await crud_payment.get_multi_filtered(
        db,
        user_id=target_user_id,
        status=status_filter,
        skip=skip,
        limit=limit,
    )
    return [PaymentResponse.model_validate(payment) for payment in payments]


async def get_payment_by_id(
    db: AsyncSession, *, payment_id: uuid.UUID, current_user: UserSession
) -> PaymentResponse:
    payment = await crud_payment.get_with_details(db, payment_id=payment_id)
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )

    if payment.booking_id is not None:
        if payment.booking is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment booking not found.",
            )
        ensure_booking_access(payment.booking, current_user)
    elif payment.series_id is not None:
        if payment.booking_series is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment series not found.",
            )
        ensure_series_access(payment.booking_series, current_user)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment owner not found.",
        )

    return PaymentResponse.model_validate(payment)
