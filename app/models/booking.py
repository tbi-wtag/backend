import uuid
from typing import TYPE_CHECKING, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    String,
    Index,
    DateTime,
    Integer,
    SmallInteger,
    Numeric,
    UUID,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampUUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.sport import Sport
    from app.models.booking_series import BookingSeries
    from app.models.booking_resource import BookingResource
    from app.models.payment import Payment


class Booking(Base, TimestampUUIDMixin):
    __tablename__: str = "bookings"

    reference: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    number_of_people: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    expired_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    sport_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sports.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    series_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("booking_series.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    user: Mapped["User"] = relationship("User", back_populates="bookings")

    sport: Mapped["Sport"] = relationship("Sport", back_populates="bookings")

    booking_series: Mapped[Optional["BookingSeries"]] = relationship(
        "BookingSeries", back_populates="bookings"
    )

    booking_resources: Mapped[list["BookingResource"]] = relationship(
        "BookingResource", back_populates="booking", cascade="all, delete-orphan"
    )

    payments: Mapped[list["Payment"]] = relationship(
        "Payment", back_populates="booking"
    )
