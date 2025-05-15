# src/core/models.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any, Dict
from uuid import UUID

class Feedback(BaseModel):
    id: UUID
    external_id: str
    source_type: str
    source_instance: Optional[str]
    tenant_id: str
    created_at: datetime
    fetched_at: Optional[datetime]
    lang: Optional[str]
    body: str
    metadata_: Dict[str, Any]

    class Config:
        orm_mode = True
