from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampUUIDMixin


class ResourceBlock(Base, TimestampUUIDMixin):
    __tablename__: str = "resource_block"

    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
