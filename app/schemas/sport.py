import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class SportBase(BaseModel):
    sport_name: str = Field(..., min_length=2, max_length=100)
    min_hours: int = Field(default=1, ge=1)
    max_hours: int = Field(default=3, ge=1)
    is_active: bool = True

    @model_validator(mode="after")
    def validate_hours(self) -> "SportBase":
        if self.min_hours is not None and self.max_hours is not None:
            if self.max_hours < self.min_hours:
                raise ValueError("max_hours must be greater than or equal to min_hours")
        return self


class SportCreate(SportBase):
    pass


class SportUpdate(SportBase):
    sport_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    min_hours: Optional[int] = Field(default=None, ge=1)
    max_hours: Optional[int] = Field(default=None, ge=1)
    is_active: Optional[bool] = None


class SportResponse(SportBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
