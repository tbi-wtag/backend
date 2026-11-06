from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, SmallInteger, CheckConstraint, Integer, Boolean 
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampUUIDMixin

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.operating_hour import OperatingHour
    from app.models.resource import Resource


class Sport(Base, TimestampUUIDMixin):
    __tablename__: str = "sports"

    sport_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    min_hours: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    max_hours: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=3)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    resources: Mapped[list["Resource"]] = relationship(
        "Resource", back_populates="sport"
    )

    operating_hours: Mapped[list["OperatingHour"]] = relationship(
        "OperatingHour", back_populates="sport", cascade="all, delete-orphan"
    )

    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="sport")

    __table_args__ = (
        CheckConstraint("min_hours > 0", name="check_min_hours_positive"),
        CheckConstraint(
            "max_hours >= min_hours", name="check_max_hours_greater_than_min_hours"
        ),
    )
