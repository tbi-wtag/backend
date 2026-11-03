import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, Numeric, String, ForeignKey, UUID, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampUUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.booking_series import BookingSeries
    from app.models.booking import Booking


class Payment(Base, TimestampUUIDMixin):
    __tablename__: str = "payments"

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    refunded_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    refunded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    series_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("booking_series.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    booking_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    user: Mapped["User"] = relationship("User", back_populates="payments")

    booking_series: Mapped[Optional["BookingSeries"]] = relationship(
        "BookingSeries", back_populates="payments"
    )

    booking: Mapped[Optional["Booking"]] = relationship(
        "Booking", back_populates="payments"
    )

    __table_args__ = (
        CheckConstraint(
            "(booking_id IS NOT NULL AND series_id IS NULL) OR "
            "(booking_id IS NULL AND series_id IS NOT NULL)",
            name="check_booking_or_series",
        ),
        CheckConstraint("amount >= 0", name="check_amount_non_negative"),
        CheckConstraint(
            "refunded_amount >= 0", name="check_refunded_amount_non_negative"
        ),
        CheckConstraint(
            "refunded_amount <= amount", name="check_refunded_amount_not_exceed_amount"
        ),
    )
