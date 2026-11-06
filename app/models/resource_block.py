import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Text, DateTime, UUID, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampUUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.resource import Resource


class ResourceBlock(Base, TimestampUUIDMixin):
    __tablename__: str = "resource_blocks"

    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    creator: Mapped[Optional["User"]] = relationship(
        "User", back_populates="resource_blocks"
    )

    resource: Mapped["Resource"] = relationship(
        "Resource", back_populates="resource_blocks"
    )

    __table_args__ = (
        CheckConstraint(
            "end_at > start_at", name="check_resource_block_end_after_start"
        ),
    )
