"""
Conversation service for managing conversations and messages
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.config.database import get_database, get_mongodb
from app.models.conversation import (
    Message,
    ConversationBase,
    ConversationDB,
    ConversationSummary,
    generate_title_from_message
)
from app.utils.logger import logger


class ConversationService:
    """Service for managing conversations"""
    
    def __init__(self):
        self.db: Optional[Union[AsyncIOMotorDatabase, Any]] = None
        self.collection_name = "conversations"
    
    def _get_collection(self):
        """Get conversations collection"""
        if self.db is None:
            self.db = get_database()
        
        # Support both MongoDB and file-based DB
        if hasattr(self.db, 'get_collection'):
            return self.db.get_collection(self.collection_name)
        else:
            # MongoDB
            return self.db[self.collection_name]
    
    async def create_conversation(
        self, 
        session_id: str, 
        user_id: str, 
        persona: str = "friend"
    ) -> Dict[str, Any]:
        """
        Create a new conversation
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
            persona: Conversation persona (default: "friend")
            
        Returns:
            Created conversation document
        """
        try:
            collection = self._get_collection()
            
            # Check if conversation already exists
            existing = await collection.find_one({"sessionId": session_id})
            if existing:
                logger.info(f"Conversation already exists: {session_id}")
                return existing
            
            # Create new conversation
            now = datetime.utcnow()
            conversation_data = {
                "sessionId": session_id,
                "userId": user_id,
                "persona": persona,
                "title": "New Conversation",
                "messages": [],
                "isActive": True,
                "lastMessageAt": now,
                "createdAt": now,
                "updatedAt": now
            }
            
            result = await collection.insert_one(conversation_data)
            conversation_data["_id"] = str(result.inserted_id)
            
            logger.info(f"Created new conversation: {session_id}")
            return conversation_data
            
        except Exception as error:
            logger.error(f"Error creating conversation: {error}")
            raise
    
    async def get_conversation(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation by session ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            Conversation document or None
        """
        try:
            collection = self._get_collection()
            return await collection.find_one({"sessionId": session_id})
        except Exception as error:
            logger.error(f"Error getting conversation: {error}")
            raise
    
    async def get_active_conversation(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get active conversation for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Active conversation document or None
        """
        try:
            collection = self._get_collection()
            
            # Use find + sort + limit for compatibility with file DB
            cursor = collection.find({"userId": user_id, "isActive": True})
            cursor = cursor.sort("lastMessageAt", -1).limit(1)
            results = await cursor.to_list(length=1)
            
            return results[0] if results else None
        except Exception as error:
            logger.error(f"Error getting active conversation: {error}")
            raise
    
    async def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add message to conversation
        
        Args:
            session_id: Session identifier
            role: Message role (user or assistant)
            content: Message content
            metadata: Optional metadata (isTranscribed, emotion, persona)
            
        Returns:
            Added message
        """
        try:
            collection = self._get_collection()
            
            conversation = await collection.find_one({"sessionId": session_id})
            if not conversation:
                raise ValueError(f"Conversation not found: {session_id}")
            
            metadata = metadata or {}
            now = datetime.utcnow()
            
            message = {
                "role": role,
                "content": content,
                "isTranscribed": metadata.get("isTranscribed", False),
                "emotion": metadata.get("emotion"),
                "persona": metadata.get("persona"),
                "timestamp": now
            }
            
            # Get current messages
            messages = conversation.get("messages", [])
            messages.append(message)
            
            # Auto-generate title from first user message
            update_data = {
                "messages": messages,
                "lastMessageAt": now,
                "updatedAt": now
            }
            
            if len(messages) == 1 and role == "user":
                title = generate_title_from_message(content)
                update_data["title"] = title
            
            await collection.update_one(
                {"sessionId": session_id},
                {"$set": update_data}
            )
            
            return message
            
        except Exception as error:
            logger.error(f"Error adding message to conversation: {error}")
            raise
    
    async def get_user_conversations(
        self, 
        user_id: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all conversations for a user
        
        Args:
            user_id: User identifier
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversation summaries
        """
        try:
            collection = self._get_collection()
            
            # Only return conversations with at least one message
            cursor = collection.find(
                {
                    "userId": user_id,
                    "messages.0": {"$exists": True}
                },
                {
                    "sessionId": 1,
                    "title": 1,
                    "messages": 1,
                    "persona": 1,
                    "lastMessageAt": 1,
                    "createdAt": 1,
                    "isActive": 1
                }
            ).sort("lastMessageAt", -1).limit(limit)
            
            conversations = await cursor.to_list(length=limit)
            
            # Filter and map conversations
            result = []
            for conv in conversations:
                messages = conv.get("messages", [])
                if messages and len(messages) > 0:
                    result.append({
                        "sessionId": conv.get("sessionId"),
                        "title": conv.get("title"),
                        "messageCount": len(messages),
                        "persona": conv.get("persona"),
                        "lastMessageAt": conv.get("lastMessageAt"),
                        "createdAt": conv.get("createdAt"),
                        "isActive": conv.get("isActive")
                    })
            
            return result
            
        except Exception as error:
            logger.error(f"Error getting user conversations: {error}")
            raise
    
    async def get_conversation_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation messages
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of messages
        """
        try:
            collection = self._get_collection()
            
            conversation = await collection.find_one({"sessionId": session_id})
            if not conversation:
                return []
            
            messages = conversation.get("messages", [])
            return [
                {
                    "role": msg.get("role"),
                    "content": msg.get("content"),
                    "isTranscribed": msg.get("isTranscribed", False),
                    "emotion": msg.get("emotion"),
                    "persona": msg.get("persona"),
                    "timestamp": msg.get("timestamp")
                }
                for msg in messages
            ]
            
        except Exception as error:
            logger.error(f"Error getting conversation messages: {error}")
            raise
    
    async def end_conversation(self, session_id: str) -> None:
        """
        Mark conversation as inactive
        
        Args:
            session_id: Session identifier
        """
        try:
            collection = self._get_collection()
            
            conversation = await collection.find_one({"sessionId": session_id})
            if conversation:
                await collection.update_one(
                    {"sessionId": session_id},
                    {
                        "$set": {
                            "isActive": False,
                            "updatedAt": datetime.utcnow()
                        }
                    }
                )
                logger.info(f"Ended conversation: {session_id}")
                
        except Exception as error:
            logger.error(f"Error ending conversation: {error}")
            raise
    
    async def update_title(self, session_id: str, title: str) -> Dict[str, Any]:
        """
        Update conversation title
        
        Args:
            session_id: Session identifier
            title: New title
            
        Returns:
            Updated conversation document
        """
        try:
            collection = self._get_collection()
            
            conversation = await collection.find_one({"sessionId": session_id})
            if not conversation:
                raise ValueError(f"Conversation not found: {session_id}")
            
            await collection.update_one(
                {"sessionId": session_id},
                {
                    "$set": {
                        "title": title,
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
            
            # Return updated conversation
            updated = await collection.find_one({"sessionId": session_id})
            return updated
            
        except Exception as error:
            logger.error(f"Error updating conversation title: {error}")
            raise
    
    async def delete_conversation(self, session_id: str) -> None:
        """
        Delete conversation
        
        Args:
            session_id: Session identifier
        """
        try:
            collection = self._get_collection()
            
            await collection.delete_one({"sessionId": session_id})
            logger.info(f"Deleted conversation: {session_id}")
            
        except Exception as error:
            logger.error(f"Error deleting conversation: {error}")
            raise
    
    async def search_conversations(
        self, 
        user_id: str, 
        query: str, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search conversations by title or message content
        
        Args:
            user_id: User identifier
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching conversation summaries
        """
        try:
            collection = self._get_collection()
            
            cursor = collection.find(
                {
                    "userId": user_id,
                    "$or": [
                        {"title": {"$regex": query, "$options": "i"}},
                        {"messages.content": {"$regex": query, "$options": "i"}}
                    ]
                }
            ).sort("lastMessageAt", -1).limit(limit)
            
            conversations = await cursor.to_list(length=limit)
            
            # Return summaries
            result = []
            for conv in conversations:
                messages = conv.get("messages", [])
                result.append({
                    "sessionId": conv.get("sessionId"),
                    "title": conv.get("title"),
                    "messageCount": len(messages),
                    "persona": conv.get("persona"),
                    "lastMessageAt": conv.get("lastMessageAt"),
                    "createdAt": conv.get("createdAt"),
                    "isActive": conv.get("isActive")
                })
            
            return result
            
        except Exception as error:
            logger.error(f"Error searching conversations: {error}")
            raise


# Singleton instance
conversation_service = ConversationService()
