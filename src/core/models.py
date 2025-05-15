from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Feedback(BaseModel):
    id: UUID
    external_id: str
    source_type: str
    source_instance: Optional[str] = None
    tenant_id: str
    created_at: datetime
    fetched_at: Optional[datetime] = None
    lang: Optional[str] = None
    body: Optional[str] = None
    metadata_: Dict[str, Any] = Field(default_factory=dict)
