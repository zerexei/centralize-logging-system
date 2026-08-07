from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class LogCreate(BaseModel):
    service: str = Field(..., json_schema_extra={"example": "chat-api"})
    environment: str = Field(..., json_schema_extra={"example": "production"})
    level: str = Field(..., json_schema_extra={"example": "ERROR"})
    log_message: str
    trace_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class LogResponse(LogCreate):
    id: str
    created_at: str
