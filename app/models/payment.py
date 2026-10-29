from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampUUIDMixin


class Payment(Base, TimestampUUIDMixin):
    __table_args__: str = "payment"

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
