import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_PITCH_FORMATS = {"5-a-side", "7-a-side", "11-a-side"}
ALLOWED_SURFACES = {"hard", "clay", "grass"}


class ResourceBase(BaseModel):
    resource_name: str = Field(..., min_length=2, max_length=50)
    pitch_format: Optional[str] = Field(default=None, max_length=50)
    surface: Optional[str] = Field(default=None, max_length=50)
    capacity: int = Field(..., gt=0)
    price_per_hour: Decimal = Field(..., ge=0, max_digits=10, decimal_places=2)
    is_active: bool = True

    @field_validator("pitch_format")
    @classmethod
    def validate_pitch_format(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in ALLOWED_PITCH_FORMATS:
            raise ValueError(
                f"pitch_format must be one of {sorted(ALLOWED_PITCH_FORMATS)}"
            )
        return normalized

    @field_validator("surface")
    @classmethod
    def validate_surface(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in ALLOWED_SURFACES:
            raise ValueError(f"surface must be one of {sorted(ALLOWED_SURFACES)}")
        return normalized


class ResourceCreate(ResourceBase):
    sport_id: uuid.UUID


class ResourceUpdate(ResourceBase):
    resource_name: Optional[str] = Field(default=None, min_length=2, max_length=50)
    pitch_format: Optional[str] = Field(default=None, max_length=50)
    surface: Optional[str] = Field(default=None, max_length=50)
    capacity: Optional[int] = Field(default=None, gt=0)
    price_per_hour: Optional[Decimal] = Field(
        default=None, ge=0, max_digits=10, decimal_places=2
    )
    is_active: Optional[bool] = None


class ResourceResponse(ResourceBase):
    id: uuid.UUID
    sport_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
