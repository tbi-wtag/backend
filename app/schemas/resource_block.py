import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ResourceBlockCreate(BaseModel):
    resource_id: uuid.UUID
    start_at: datetime
    end_at: datetime
    reason: str = Field(..., min_length=1, max_length=500)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("reason cannot be empty or whitespace")
        return cleaned

    @model_validator(mode="after")
    def validate_time_range(self) -> "ResourceBlockCreate":
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be strictly after start_at")
        return self


class ResourceBlockResponse(BaseModel):
    id: uuid.UUID
    resource_id: uuid.UUID
    start_at: datetime
    end_at: datetime
    reason: str
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
