from typing import Any, Dict, Optional
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuditLogBase(BaseModel):
    action: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    status: str = "SUCCESS"
    details: Optional[Dict[str, Any]] = None


class AuditLogCreate(AuditLogBase):
    pass


class AuditLogUpdate(BaseModel):
    pass


class AuditLogResponse(AuditLogBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
