"""
Memory model for MongoDB
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.config.constants import MemoryTag, SentimentType


class MemoryContext(BaseModel):
    """Memory context information"""
    model_config = ConfigDict(populate_by_name=True)
    
    persona: Optional[str] = None
    related_topics: List[str] = Field(default_factory=list, alias="relatedTopics")
    conversation_snippet: Optional[str] = Field(None, alias="conversationSnippet")


class MemoryMetadata(BaseModel):
    """Memory metadata"""
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat() + 'Z'}
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")
    access_count: int = Field(0, alias="accessCount")
    last_accessed: Optional[datetime] = Field(None, alias="lastAccessed")


class MemoryBase(BaseModel):
    """Base memory schema"""
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat() + 'Z'}
    )
    
    session_id: str = Field(..., alias="sessionId")
    user_id: str = Field("anonymous", alias="userId")
    title: str
    content: str
    summary: Optional[str] = None
    emotion: str = "neutral"
    sentiment: SentimentType = SentimentType.NEUTRAL
    tags: List[MemoryTag] = Field(default_factory=list)
    importance: int = Field(5, ge=0, le=10)
    context: MemoryContext = Field(default_factory=MemoryContext)
    metadata: MemoryMetadata = Field(default_factory=MemoryMetadata)


class MemoryDB(MemoryBase):
    """Memory schema with MongoDB ID"""
    id: Optional[str] = Field(None, alias="_id")


class MemoryCreate(BaseModel):
    """Schema for creating a memory"""
    session_id: str
    user_id: str
    title: str
    content: str
    summary: Optional[str] = None
    emotion: str = "neutral"
    sentiment: SentimentType = SentimentType.NEUTRAL
    tags: List[MemoryTag] = Field(default_factory=list)
    importance: int = Field(5, ge=0, le=10)
    context: Optional[MemoryContext] = None


class MemoryUpdate(BaseModel):
    """Schema for updating a memory"""
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    emotion: Optional[str] = None
    sentiment: Optional[SentimentType] = None
    tags: Optional[List[MemoryTag]] = None
    importance: Optional[int] = Field(None, ge=0, le=10)
    context: Optional[MemoryContext] = None


def memory_to_dict(memory: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert MongoDB document to dictionary
    
    Args:
        memory: MongoDB document
        
    Returns:
        Dictionary representation
    """
    if '_id' in memory:
        memory['_id'] = str(memory['_id'])
    
    return memory
