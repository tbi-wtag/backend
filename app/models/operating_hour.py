import uuid
from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import (
    SmallInteger,
    Time,
    ForeignKey,
    UUID,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampUUIDMixin

if TYPE_CHECKING:
    from app.models.sport import Sport


class OperatingHour(Base, TimestampUUIDMixin):
    __tablename__: str = "operating_hours"

    weekday: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    open_time: Mapped[time] = mapped_column(Time, nullable=False)
    close_time: Mapped[time] = mapped_column(Time, nullable=False)

    sport_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sport: Mapped["Sport"] = relationship("Sport", back_populates="operating_hours")

    __table_args__ = (
        UniqueConstraint(
            "sport_id", "weekday", name="uq_operating_hours_sport_weekday"
        ),
        CheckConstraint(
            "open_time < close_time", name="check_open_time_before_close_time"
        ),
        CheckConstraint("weekday >= 0 AND weekday <= 6", name="check_weekday_range"),
    )
