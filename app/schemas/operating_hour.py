import uuid
from datetime import datetime, time
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class OperatingHourBase(BaseModel):
    weekday: int = Field(..., ge=0, le=6, description="0=Monday through 6=Sunday")
    open_time: time
    close_time: time

    @model_validator(mode="after")
    def validate_time_order(self) -> "OperatingHourBase":
        if self.open_time >= self.close_time:
            raise ValueError("open_time must be strictly before close_time")
        return self


class OperatingHourCreate(OperatingHourBase):
    pass


class OperatingHourUpdate(OperatingHourBase):
    pass


class WeeklyOperatingHoursUpdate(BaseModel):
    schedule: list[OperatingHourCreate] = Field(..., max_length=7)

    @model_validator(mode="after")
    def validate_unique_weekdays(self) -> "WeeklyOperatingHoursUpdate":
        weekdays = [item.weekday for item in self.schedule]
        if len(weekdays) != len(set(weekdays)):
            raise ValueError(
                "Duplicate weekdays are not allowed in the weekly schedule"
            )
        return self


class OperatingHourResponse(OperatingHourBase):
    id: uuid.UUID
    sport_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
