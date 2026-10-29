from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import SmallInteger, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampUUIDMixin


class OperatingHour(Base, TimestampUUIDMixin):
    __tablename__: str = "operating_hours"

    weekday: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    open_time: Mapped[time] = mapped_column(Time, nullable=False)
    close_time: Mapped[time] = mapped_column(Time, nullable=False)
