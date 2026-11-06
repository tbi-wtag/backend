import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SessionBase(BaseModel):
    user_id: uuid.UUID
    expires_at: datetime


class SessionCreate(SessionBase):
    pass


class SessionResponse(SessionBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
