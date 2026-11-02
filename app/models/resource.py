import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Integer, Boolean, Numeric, UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal

from app.db.base import Base, TimestampUUIDMixin

if TYPE_CHECKING:
    from app.models.sport import Sport
    from app.models.resource_block import ResourceBlock
    from app.models.booking_resource import BookingResource


class Resource(Base, TimestampUUIDMixin):
    __tablename__: str = "resources"

    resource_name: Mapped[str] = mapped_column(String(50), nullable=False)
    pitch_format: Mapped[str] = mapped_column(String(50), nullable=True)
    surface: Mapped[str] = mapped_column(String(50), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    price_per_hour: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    sport_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sports.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    sport: Mapped["Sport"] = relationship("Sport", back_populates="resources")

    resource_blocks: Mapped[list["ResourceBlock"]] = relationship(
        "ResourceBlock", back_populates="resource", cascade="all, delete-orphan"
    )

    booking_resources: Mapped[list["BookingResource"]] = relationship(
        "BookingResource", back_populates="resource"
    )
