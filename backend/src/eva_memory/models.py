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


class ExtractedFact(BaseModel):
    fact: str
    category: str
    subcategory: Optional[str] = None
    source_role: Optional[str] = None
    time_scope: Optional[str] = None
    importance: Optional[str] = None
    confidence: Optional[float] = None
    tags: Optional[List[str]] = None


class MemoryChange(BaseModel):
    event: str  # "ADD" | "UPDATE" | "DELETE"
    memory_id: Optional[str] = None
    old_text: Optional[str] = None
    new_text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


