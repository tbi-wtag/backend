import uuid
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import (
    DateTime,
    Boolean,
    ForeignKey,
    UUID,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampUUIDMixin

if TYPE_CHECKING:
    from app.models.resource import Resource
    from app.models.booking import Booking


class BookingResource(Base, TimestampUUIDMixin):
    __tablename__: str = "booking_resources"

    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    resource: Mapped["Resource"] = relationship(
        "Resource", back_populates="booking_resources"
    )

    booking: Mapped["Booking"] = relationship(
        "Booking", back_populates="booking_resources"
    )

    __table_args__ = (
        UniqueConstraint("booking_id", "resource_id", name="unique_booking_resource"),
        CheckConstraint(
            "end_at > start_at", name="check_booking_resources_end_after_start"
        ),
    )
