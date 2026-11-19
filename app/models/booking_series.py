import uuid
from typing import TYPE_CHECKING, List
from datetime import date

from sqlalchemy import Date, UUID, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampUUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.booking import Booking
    from app.models.payment import Payment


class BookingSeries(Base, TimestampUUIDMixin):
    __tablename__: str = "booking_series"

    start_at: Mapped[date] = mapped_column(Date, nullable=False)
    end_at: Mapped[date] = mapped_column(Date, nullable=False)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    user: Mapped["User"] = relationship("User", back_populates="booking_series")

    bookings: Mapped[List["Booking"]] = relationship(
        "Booking", back_populates="booking_series"
    )

    payments: Mapped[List["Payment"]] = relationship(
        "Payment", back_populates="booking_series"
    )

    __table_args__ = (
        CheckConstraint(
            "end_at > start_at", name="check_booking_series_end_after_start"
        ),
    )
