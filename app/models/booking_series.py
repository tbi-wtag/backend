from typing import TYPE_CHECKING
from datetime import date

from sqlalchemy import Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampUUIDMixin


class bookingSeries(Base, TimestampUUIDMixin):
    __tablename__: str = "booking_series"

    start_at: Mapped[date] = mapped_column(Date, nullable=False)
    end_at: Mapped[date] = mapped_column(Date, nullable=False)
