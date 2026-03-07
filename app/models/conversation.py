"""
Conversation model for MongoDB
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from bson import ObjectId


class Message(BaseModel):
    """Message schema"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat() + 'Z'}
    )
    
    role: str
    content: str
    is_transcribed: bool = False
    emotion: Optional[str] = None
    persona: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in ['user', 'assistant']:
            raise ValueError('role must be user or assistant')
        return v


class ConversationBase(BaseModel):
    """Base conversation schema"""
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat() + 'Z'}
    )
    
    session_id: str = Field(..., alias="sessionId")
    user_id: str = Field(..., alias="userId")
    title: str = "New Conversation"
    messages: List[Message] = Field(default_factory=list)
    persona: str = "friend"
    is_active: bool = Field(True, alias="isActive")
    last_message_at: datetime = Field(default_factory=datetime.utcnow, alias="lastMessageAt")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")


class ConversationDB(ConversationBase):
    """Conversation schema with MongoDB ID"""
    id: Optional[str] = Field(None, alias="_id")


class ConversationCreate(BaseModel):
    """Schema for creating a conversation"""
    session_id: str
    user_id: str
    persona: str = "friend"


class ConversationSummary(BaseModel):
    """Conversation summary for list view"""
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat() + 'Z'}
    )
    
    session_id: str = Field(..., alias="sessionId")
    title: str
    message_count: int = Field(..., alias="messageCount")
    persona: str
    last_message_at: datetime = Field(..., alias="lastMessageAt")
    created_at: datetime = Field(..., alias="createdAt")
    is_active: bool = Field(..., alias="isActive")


def generate_title_from_message(content: str) -> str:
    """
    Generate conversation title from first message
    
    Args:
        content: Message content
        
    Returns:
        Generated title
    """
    if len(content) > 50:
        return content[:50] + "..."
    return content


def conversation_to_dict(conversation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert MongoDB document to dictionary
    
    Args:
        conversation: MongoDB document
        
    Returns:
        Dictionary representation
    """
    if '_id' in conversation:
        conversation['_id'] = str(conversation['_id'])
    
    return conversation
