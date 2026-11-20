import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.core.config import settings


class PriceQuoteRequest(BaseModel):
    sport_id: uuid.UUID
    start_at: datetime
    duration_minutes: int = Field(
        default=settings.booking.default_slot_duration_minutes, gt=0, le=720
    )
    number_of_people: int = Field(default=1, gt=0)
    resource_ids: Optional[list[uuid.UUID]] = None
    pitch_format: Optional[str] = Field(default=None, max_length=50)
    surface: Optional[str] = Field(default=None, max_length=50)

    @field_validator("pitch_format", "surface")
    @classmethod
    def strip_optional_strings(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned if cleaned else None


class PriceQuoteResponse(BaseModel):
    sport_id: uuid.UUID
    start_at: datetime
    end_at: datetime
    duration_minutes: int
    number_of_people: int
    resource_ids: list[uuid.UUID]
    total_price: Decimal
