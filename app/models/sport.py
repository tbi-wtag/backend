from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampUUIDMixin


class Sport(Base, TimestampUUIDMixin):
    __tablename__: str = "sports"

    sport_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    min_hours: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    max_hours: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=3)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
