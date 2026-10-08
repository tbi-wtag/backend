# 1. Standard Library Imports
import uuid
from datetime import datetime

# 2. SQLAlchemy Core Types & PostgreSQL Dialect
from sqlalchemy import DateTime, text
from sqlalchemy.dialects.postgresql import UUID

# 3. SQLAlchemy ORM Declarative & Mapping Tools
from sqlalchemy.orm import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

class TimestampUUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
        server_default=text("now()"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
        server_default=text("now()"),
    )
