from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Integer, Boolean, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from decimal import Decimal

from app.db.base import Base, TimestampUUIDMixin

class Resource(Base, TimestampUUIDMixin):
    __tablename__: str = "resources"

    resource_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)
    pitch_format: Mapped[str] = mapped_column(String(50), unique=True, nullable=True)
    surface: Mapped[str] = mapped_column(String(50), unique=True, nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    price_per_hour: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)