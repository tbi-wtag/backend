import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.booking import crud_booking
from app.crud.resource import crud_resource
from app.crud.resource_block import crud_resource_block
from app.models.booking import Booking
from app.models.booking_resource import BookingResource
from app.schemas.auth import UserSession
from app.schemas.booking import BookingCreate, BookingResponse
from app.schemas.enums import UserRole
from app.services import pricing_service, slot_service
from app.services.audit_service import audit_service
from app.services.booking_helpers import (
    apply_refund_if_eligible,
    ensure_booking_access,
    generate_booking_reference,
    to_booking_response,
)


async def create_booking(
    db: AsyncSession,
    *,
    booking_in: BookingCreate,
    current_user: UserSession,
    request: Optional[Request] = None,
) -> BookingResponse:
    allocated, slot_start, slot_end = await slot_service.resolve_and_validate_resources(
        db,
        sport_id=booking_in.sport_id,
        start_at=booking_in.start_at,
        duration_minutes=booking_in.duration_minutes,
        number_of_people=booking_in.number_of_people,
        resource_ids=booking_in.resource_ids,
        pitch_format=booking_in.pitch_format,
        surface=booking_in.surface,
    )
    resource_ids = [r.id for r in allocated]

    locked_resources = await crud_resource.lock_active_by_ids(
        db, resource_ids=resource_ids
    )
    if len(locked_resources) != len(resource_ids):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One or more selected resources are no longer active.",
        )

    now_utc = datetime.now(timezone.utc)
    overlapping_bookings = await crud_booking.get_overlapping_booking_resources(
        db,
        resource_ids=resource_ids,
        start_at=slot_start,
        end_at=slot_end,
        now_utc=now_utc,
    )
    overlapping_blocks = await crud_resource_block.get_overlapping_for_resources(
        db,
        resource_ids=resource_ids,
        start_at=slot_start,
        end_at=slot_end,
    )
    if overlapping_bookings or overlapping_blocks:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One or more selected resources are no longer available for this slot.",
        )

    total_price = pricing_service.calculate_total_price(
        locked_resources, booking_in.duration_minutes
    )
    booking = Booking(
        reference=generate_booking_reference(now_utc),
        user_id=current_user.user_id,
        sport_id=booking_in.sport_id,
        start_at=slot_start,
        end_at=slot_end,
        duration_minutes=booking_in.duration_minutes,
        number_of_people=booking_in.number_of_people,
        status="pending",
        total_price=total_price,
        expired_at=now_utc
        + timedelta(minutes=settings.booking.pending_payment_hold_minutes),
    )
    db.add(booking)
    await db.flush()

    db.add_all(
        BookingResource(
            booking_id=booking.id,
            resource_id=rid,
            start_at=slot_start,
            end_at=slot_end,
            is_active=True,
        )
        for rid in resource_ids
    )

    await db.commit()
    created = await crud_booking.get_with_details(db, booking_id=booking.id)
    assert created is not None
    return to_booking_response(created)


async def list_bookings(
    db: AsyncSession,
    *,
    current_user: UserSession,
    sport_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = None,
    start_from: Optional[datetime] = None,
    start_to: Optional[datetime] = None,
    user_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[BookingResponse]:
    target_user_id = (
        user_id if current_user.role == UserRole.ADMIN else current_user.user_id
    )
    bookings = await crud_booking.get_multi_filtered(
        db,
        user_id=target_user_id,
        sport_id=sport_id,
        status=status_filter,
        start_from=start_from,
        start_to=start_to,
        skip=skip,
        limit=limit,
    )
    return [to_booking_response(b) for b in bookings]


async def get_booking_by_id(
    db: AsyncSession,
    *,
    booking_id: uuid.UUID,
    current_user: UserSession,
) -> BookingResponse:
    booking = await crud_booking.get_with_details(db, booking_id=booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found.",
        )

    ensure_booking_access(booking, current_user)
    return to_booking_response(booking)


async def cancel_booking(
    db: AsyncSession,
    *,
    booking_id: uuid.UUID,
    current_user: UserSession,
    request: Optional[Request] = None,
) -> BookingResponse:
    booking = await crud_booking.get_with_details(db, booking_id=booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found.",
        )

    ensure_booking_access(booking, current_user)

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

    was_paid = any(p.status == "paid" for p in booking.payments)

    booking.status = "cancelled"
    booking.cancelled_at = now_utc
    for br in booking.booking_resources:
        br.is_active = False

    refund_initiated = apply_refund_if_eligible(booking, now_utc)

    if was_paid:
        await audit_service.log_event(
            db=db,
            action="BOOKING_CANCEL",
            user_id=str(current_user.user_id),
            request=request,
            status="SUCCESS",
            details={
                "booking_id": str(booking.id),
                "reference": booking.reference,
                "refund_initiated": refund_initiated,
            },
            flush=True,
        )

    await db.commit()
    updated = await crud_booking.get_with_details(db, booking_id=booking.id)
    assert updated is not None
    return to_booking_response(updated)
