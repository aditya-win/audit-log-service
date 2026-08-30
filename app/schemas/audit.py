from pydantic import BaseModel, Field, model_validator, ConfigDict
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

class EventType(str, Enum):
    USER_LOGIN = "USER_LOGIN"
    RECORD_UPDATED = "RECORD_UPDATED"
    PERMISSION_GRANTED = "PERMISSION_GRANTED"
    DATA_ACCESS = "DATA_ACCESS"

class AuditEventCreate(BaseModel):

    eventType: EventType
    actorId: str = Field(..., min_length=1, max_length=128)
    resourceType: str = Field(..., min_length=1, max_length=128)
    resourceId: str = Field(..., min_length=1, max_length=128)
    payload: Dict[str, Any]
    timestamp: Optional[datetime] = None

    @model_validator(mode='after')
    def validate_payload_size(self):
        # basic check to ensure payload isn't massive (e.g. over 100 keys or string length over 10000)
        if len(str(self.payload)) > 10000:
            raise ValueError("Payload is oversized")
        return self

class AuditEventResponse(BaseModel):
    id: int
    eventType: EventType
    actorId: str
    resourceType: str
    resourceId: str
    payload: Dict[str, Any]
    timestamp: datetime
    previousHash: str
    currentHash: str

class AuditEventQuery(BaseModel):
    actorId: Optional[str] = Field(None, max_length=128)
    resourceType: Optional[str] = Field(None, max_length=128)
    resourceId: Optional[str] = Field(None, max_length=128)
    eventType: Optional[EventType] = None
    from_date: Optional[datetime] = Field(None, alias="from")
    to_date: Optional[datetime] = Field(None, alias="to")
    page: int = Field(1, ge=1)
    pageSize: int = Field(10, ge=1, le=100)

    @model_validator(mode='after')
    def validate_date_range(self):
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise ValueError("'from' date cannot be after 'to' date")
        return self
