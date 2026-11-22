import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.config import settings
from app.schemas.booking import BookingResponse


class MonthlyBookingCreate(BaseModel):
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


class SeriesPaymentSummary(BaseModel):
    id: uuid.UUID
    amount: Decimal
    status: str
    paid_at: Optional[datetime] = None
    refunded_amount: Decimal
    refunded_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SeriesClashDetail(BaseModel):
    date: date
    start_at: datetime
    end_at: datetime
    reason: str


class BookingSeriesResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    start_at: date
    end_at: date
    total_price: Decimal
    payment: Optional[SeriesPaymentSummary] = None
    created_at: datetime
    bookings: list[BookingResponse]
