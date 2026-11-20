import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AvailableResourceResponse(BaseModel):
    id: uuid.UUID
    resource_name: str
    pitch_format: Optional[str] = None
    surface: Optional[str] = None
    capacity: int
    price_per_hour: Decimal

    model_config = ConfigDict(from_attributes=True)


class AvailableSlotResponse(BaseModel):
    start_at: datetime
    end_at: datetime
    duration_minutes: int
    available_resources: list[AvailableResourceResponse]


class SlotSearchResponse(BaseModel):
    sport_id: uuid.UUID
    search_date: date
    duration_minutes: int
    slots: list[AvailableSlotResponse]
