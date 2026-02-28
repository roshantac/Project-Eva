from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class MemoryRecord(BaseModel):
    memory_id: str
    user_id: str
    text: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: Optional[str] = None
    is_deleted: bool = False


class SearchHit(BaseModel):
    memory: MemoryRecord
    score: float

