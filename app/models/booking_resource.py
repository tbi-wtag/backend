from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampUUIDMixin

class bookingResource(Base,TimestampUUIDMixin):
    __tablename__: str = "booking_resource"

    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True) 
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)