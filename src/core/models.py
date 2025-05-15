# src/core/models.py
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


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
