from typing import TYPE_CHECKING, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Index, DateTime, Integer, SmallInteger, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampUUIDMixin

class Booking(Base, TimestampUUIDMixin):
    __tablename__: str = "bookings"

    reference: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True) 
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    number_of_people: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    expired_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True,index=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True,)
