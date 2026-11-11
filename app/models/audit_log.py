from sqlalchemy import JSON,  String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampUUIDMixin


class AuditLog(Base, TimestampUUIDMixin):
    __tablename__: str = "audit_logs"

    action: Mapped[str] = mapped_column(String(50), index=True)
    user_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="SUCCESS", server_default="SUCCESS")
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
