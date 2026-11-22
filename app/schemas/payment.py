import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PaymentProcessRequest(BaseModel):
    card_number: str
    cardholder_name: Optional[str] = Field(default=None, max_length=100)

    @field_validator("card_number")
    @classmethod
    def validate_card_number(cls, value: str) -> str:
        digits = value.replace(" ", "")
        if not digits.isdigit() or not (12 <= len(digits) <= 19):
            raise ValueError("card_number must be 12 to 19 digits")
        return digits

    @field_validator("cardholder_name")
    @classmethod
    def strip_cardholder_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned if cleaned else None


class PaymentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    booking_id: Optional[uuid.UUID] = None
    series_id: Optional[uuid.UUID] = None
    amount: Decimal
    status: str
    paid_at: Optional[datetime] = None
    refunded_amount: Decimal
    refunded_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
