import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampUUIDMixin

if TYPE_CHECKING:
    from app.models.user import User  

class Session(Base, TimestampUUIDMixin):
    __tablename__:str = "sessions"

    user_id:Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    session_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="session")
