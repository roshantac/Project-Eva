"""
Memory management engine for short-term and long-term memory
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.config.database import get_database, get_redis
from app.config.constants import MAX_SHORT_TERM_MEMORY, MemoryTag
from app.utils.logger import logger


class MemoryEngine:
    """Engine for managing conversation memory"""
    
    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.short_term_memory: Dict[str, Dict[str, Any]] = {}
        
        self.valid_tags = ['goal', 'achievement', 'emotional_moment', 'important', 'casual']
        self.tag_mapping = {
            'emotional breakthrough': 'emotional_moment',
            'emotional_breakthrough': 'emotional_moment',
            'breakthrough': 'emotional_moment',
            'emotion': 'emotional_moment',
            'emotional': 'emotional_moment',
            'decision': 'important',
            'insight': 'important',
            'realization': 'important',
            'milestone': 'achievement',
            'success': 'achievement',
            'accomplishment': 'achievement',
            'aspiration': 'goal',
            'objective': 'goal',
            'target': 'goal',
            'plan': 'goal'
        }
    
    def _get_collection(self, collection_name: str):
        """Get collection from database (supports both MongoDB and file-based)"""
        db = get_database()
        
        # Support both MongoDB and file-based DB
        if hasattr(db, 'get_collection'):
            return db.get_collection(collection_name)
        else:
            return db[collection_name]
    
    def normalize_tags(self, tags: Optional[List[str]]) -> List[str]:
        """
        Normalize tags to valid enum values
        
        Args:
            tags: List of tag strings
            
        Returns:
            List of normalized valid tags
        """
        if not isinstance(tags, list):
            return [MemoryTag.CASUAL.value]
        
        normalized = []
        for tag in tags:
            normalized_tag = tag.lower().strip().replace(' ', '_')
            
            if normalized_tag in self.valid_tags:
                normalized.append(normalized_tag)
            else:
                mapped_tag = self.tag_mapping.get(tag.lower().strip()) or \
                            self.tag_mapping.get(normalized_tag)
                
                if mapped_tag:
                    normalized.append(mapped_tag)
                else:
                    normalized.append(MemoryTag.CASUAL.value)
        
        return list(dict.fromkeys(normalized))
    
    async def initialize_session(
        self,
        session_id: str,
        user_id: str = 'anonymous'
    ) -> Optional[Dict[str, Any]]:
        """
        Initialize memory session
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            
        Returns:
            Conversation document or None
        """
        try:
            conversations_collection = self._get_collection('conversations')
            
            conversation = await conversations_collection.find_one({'sessionId': session_id})
            
            if not conversation:
                self.short_term_memory[session_id] = {
                    'messages': [],
                    'persona': 'friend',
                    'context': {}
                }
            else:
                messages = conversation.get('messages', [])
                recent_messages = messages[-MAX_SHORT_TERM_MEMORY:] if messages else []
                
                self.short_term_memory[session_id] = {
                    'messages': [
                        {
                            'role': msg.get('role'),
                            'content': msg.get('content'),
                            'emotion': msg.get('emotion'),
                            'timestamp': msg.get('timestamp')
                        }
                        for msg in recent_messages
                    ],
                    'persona': conversation.get('persona', 'friend'),
                    'context': {}
                }
            
            logger.info(f"Memory session initialized: {session_id}")
            return conversation
        except Exception as error:
            logger.error(f'Error initializing memory session: {error}')
            raise
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        emotion: str = 'neutral',
        sentiment: str = 'neutral'
    ) -> bool:
        """
        Add message to short-term memory
        
        Args:
            session_id: Session identifier
            role: Message role (user or assistant)
            content: Message content
            emotion: Detected emotion
            sentiment: Detected sentiment
            
        Returns:
            True if successful
        """
        try:
            session_memory = self.short_term_memory.get(session_id)
            if session_memory:
                message = {
                    'role': role,
                    'content': content,
                    'emotion': emotion,
                    'sentiment': sentiment,
                    'timestamp': datetime.utcnow()
                }
                
                session_memory['messages'].append(message)
                
                if len(session_memory['messages']) > MAX_SHORT_TERM_MEMORY:
                    session_memory['messages'] = session_memory['messages'][-MAX_SHORT_TERM_MEMORY:]
                
                redis_client = get_redis()
                if redis_client:
                    await redis_client.setex(
                        f"session:{session_id}",
                        3600,
                        json.dumps(session_memory, default=str)
                    )
            
            return True
        except Exception as error:
            logger.error(f'Error adding message to memory: {error}')
            raise
    
    def get_short_term_memory(self, session_id: str) -> Dict[str, Any]:
        """
        Get short-term memory for session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Short-term memory dictionary
        """
        return self.short_term_memory.get(session_id, {
            'messages': [],
            'persona': 'friend',
            'context': {}
        })
    
    async def get_conversation_context(self, session_id: str, limit: int = 10) -> str:
        """
        Get conversation context as formatted string
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to include
            
        Returns:
            Formatted conversation context
        """
        try:
            session_memory = self.get_short_term_memory(session_id)
            recent_messages = session_memory['messages'][-limit:] if session_memory['messages'] else []
            
            context = '\n'.join([
                f"{msg['role']}: {msg['content']}"
                for msg in recent_messages
            ])
            
            return context
        except Exception as error:
            logger.error(f'Error getting conversation context: {error}')
            return ''
    
    async def save_long_term_memory(
        self,
        session_id: str,
        user_id: str,
        memory_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save memory to long-term storage
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            memory_data: Memory data to save
            
        Returns:
            Saved memory document
        """
        try:
            memories_collection = self._get_collection('memories')
            
            now = datetime.utcnow()
            memory_doc = {
                'sessionId': session_id,
                'userId': user_id,
                'title': memory_data.get('title'),
                'content': memory_data.get('content'),
                'summary': memory_data.get('summary'),
                'emotion': memory_data.get('emotion', 'neutral'),
                'sentiment': memory_data.get('sentiment', 'neutral'),
                'tags': memory_data.get('tags', [MemoryTag.CASUAL.value]),
                'importance': memory_data.get('importance', 5),
                'context': {
                    'persona': memory_data.get('persona'),
                    'relatedTopics': memory_data.get('relatedTopics', []),
                    'conversationSnippet': memory_data.get('conversationSnippet')
                },
                'metadata': {
                    'createdAt': now,
                    'updatedAt': now,
                    'accessCount': 0,
                    'lastAccessed': None
                }
            }
            
            result = await memories_collection.insert_one(memory_doc)
            memory_doc['_id'] = str(result.inserted_id)
            
            logger.info(f"Long-term memory saved: {memory_doc['_id']}")
            return memory_doc
        except Exception as error:
            logger.error(f'Error saving long-term memory: {error}')
            raise
    
    async def get_long_term_memories(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get long-term memories for user
        
        Args:
            user_id: User identifier
            limit: Maximum number of memories to return
            
        Returns:
            List of memory documents
        """
        try:
            memories_collection = self._get_collection('memories')
            
            cursor = memories_collection.find(
                {'userId': user_id}
            ).sort('metadata.createdAt', -1).limit(limit)
            
            memories = await cursor.to_list(length=limit)
            
            for memory in memories:
                if '_id' in memory:
                    memory['_id'] = str(memory['_id'])
            
            return memories
        except Exception as error:
            logger.error(f'Error retrieving long-term memories: {error}')
            return []
    
    def _memory_relevance_score(self, memory: Dict[str, Any], query_words: List[str]) -> int:
        """
        Score memory by query words. Title matches rank much higher so e.g.
        "Reminding User of Mom's Birthday" beats a memory that only mentions mom in content.
        """
        if not query_words:
            return 0
        title = ((memory.get('title') or '') + ' ').lower()
        summary = ((memory.get('summary') or '') + ' ').lower()
        content = ((memory.get('content') or '') + ' ').lower()
        score = 0
        for w in query_words:
            if not w or len(w) < 2:
                continue
            wl = w.lower()
            if wl in title:
                score += 10
            if wl in summary:
                score += 3
            if wl in content:
                score += 1
        return score

    async def get_relevant_memories(
        self,
        user_id: str,
        current_context: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get relevant memories for the user. Uses keyword matching from current_context
        when provided; otherwise returns most recent by importance and date.
        Works with both MongoDB and file-based DB (no $gte filter).
        """
        try:
            memories_collection = self._get_collection('memories')
            # Query by userId only so file DB works (no $gte)
            cursor = memories_collection.find({'userId': user_id})
            # Fetch more so we can rank by relevance; sort by importance (file DB supports single key)
            memories = await cursor.sort('importance', -1).to_list(length=50)

            if not memories:
                logger.debug(f'No long-term memories found for user_id={user_id}')
                return []

            for m in memories:
                if '_id' in m and not isinstance(m['_id'], str):
                    m['_id'] = str(m['_id'])

            # If we have current message, prefer memories that mention similar words (e.g. "mom birthday" -> "Mom's Birthday")
            query_words = []
            if current_context and isinstance(current_context, str):
                query_words = [w.strip() for w in current_context.replace("'", " ").split() if len(w.strip()) > 1]

            if query_words:
                scored = [(self._memory_relevance_score(m, query_words), m) for m in memories]
                scored.sort(key=lambda x: (-x[0], -(x[1].get('importance') or 0)))
                relevant_memories = [m for s, m in scored if s > 0][:limit]
                # If no keyword match, fall back to top by importance
                if not relevant_memories:
                    relevant_memories = [m for _, m in scored[:limit]]
                if relevant_memories and scored[0][0] > 0:
                    logger.info(f'Memory Lane: using {len(relevant_memories)} relevant memories for query (top match: "{relevant_memories[0].get("title", "")}")')
            else:
                relevant_memories = memories[:limit]

            # Update access metadata (best-effort; file DB supports update_one)
            for memory in relevant_memories:
                metadata = memory.get('metadata', {}) or {}
                metadata['accessCount'] = metadata.get('accessCount', 0) + 1
                metadata['lastAccessed'] = datetime.utcnow()
                try:
                    await memories_collection.update_one(
                        {'_id': memory['_id']},
                        {'$set': {'metadata': metadata}}
                    )
                except Exception:
                    pass

            return relevant_memories
        except Exception as error:
            logger.error(f'Error getting relevant memories: {error}')
            return []
    
    async def search_memories(self, user_id: str, search_text: str) -> List[Dict[str, Any]]:
        """
        Search memories by text
        
        Args:
            user_id: User identifier
            search_text: Search query
            
        Returns:
            List of matching memory documents
        """
        try:
            memories_collection = self._get_collection('memories')
            
            cursor = memories_collection.find({
                'userId': user_id,
                '$or': [
                    {'title': {'$regex': search_text, '$options': 'i'}},
                    {'content': {'$regex': search_text, '$options': 'i'}},
                    {'summary': {'$regex': search_text, '$options': 'i'}}
                ]
            }).sort('metadata.createdAt', -1)
            
            memories = await cursor.to_list(length=None)
            
            for memory in memories:
                if '_id' in memory:
                    memory['_id'] = str(memory['_id'])
            
            return memories
        except Exception as error:
            logger.error(f'Error searching memories: {error}')
            return []
    
    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update memory document
        
        Args:
            memory_id: Memory identifier
            updates: Dictionary of fields to update
            
        Returns:
            Updated memory document
        """
        try:
            from bson import ObjectId
            
            memories_collection = self._get_collection('memories')
            
            memory = await memories_collection.find_one({'_id': ObjectId(memory_id)})
            if not memory:
                raise ValueError('Memory not found')
            
            updates['metadata.updatedAt'] = datetime.utcnow()
            
            await memories_collection.update_one(
                {'_id': ObjectId(memory_id)},
                {'$set': updates}
            )
            
            updated_memory = await memories_collection.find_one({'_id': ObjectId(memory_id)})
            if '_id' in updated_memory:
                updated_memory['_id'] = str(updated_memory['_id'])
            
            logger.info(f"Memory updated: {memory_id}")
            return updated_memory
        except Exception as error:
            logger.error(f'Error updating memory: {error}')
            raise
    
    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete memory document
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            True if successful
        """
        try:
            from bson import ObjectId
            
            memories_collection = self._get_collection('memories')
            
            await memories_collection.delete_one({'_id': ObjectId(memory_id)})
            logger.info(f"Memory deleted: {memory_id}")
            return True
        except Exception as error:
            logger.error(f'Error deleting memory: {error}')
            raise
    
    async def analyze_and_save_important_moments(
        self,
        session_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze conversation for important moments and save to long-term memory
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            
        Returns:
            Saved memory document or None
        """
        try:
            conversations_collection = self._get_collection('conversations')
            
            conversation = await conversations_collection.find_one({'sessionId': session_id})
            if not conversation or len(conversation.get('messages', [])) < 5:
                return None
            
            messages = conversation.get('messages', [])
            recent_messages = messages[-20:] if len(messages) > 20 else messages
            conversation_text = '\n'.join([
                f"{msg.get('role')}: {msg.get('content')}"
                for msg in recent_messages
            ])
            
            prompt = f"""Analyze this conversation and identify if there are any important moments worth saving to long-term memory.

Important moments include:
- Goals or aspirations mentioned
- Significant achievements
- Emotional breakthroughs or vulnerable moments
- Important decisions
- Meaningful insights or realizations

Conversation:
{conversation_text}

If there's an important moment, respond with JSON:
{{
  "hasImportantMoment": true,
  "title": "Brief title",
  "summary": "Summary of the moment",
  "importance": 7,
  "tags": ["goal", "achievement", "emotional_moment", "important", "casual"],
  "relatedTopics": ["topic1", "topic2"]
}}

IMPORTANT: Use ONLY these exact tags: "goal", "achievement", "emotional_moment", "important", "casual"

If no important moment, respond with: {{"hasImportantMoment": false}}"""

            response = await self.llm_service.generate_completion([
                {'role': 'system', 'content': 'You are a memory analyzer. Respond only with valid JSON.'},
                {'role': 'user', 'content': prompt}
            ], {
                'temperature': 0.3,
                'max_tokens': 300
            })

            analysis = json.loads(response)
            
            if analysis.get('hasImportantMoment'):
                normalized_tags = self.normalize_tags(analysis.get('tags', []))
                
                conversation_snippet = ' '.join([
                    msg.get('content', '')
                    for msg in recent_messages[-3:]
                ])
                
                memory = await self.save_long_term_memory(session_id, user_id, {
                    'title': analysis.get('title'),
                    'content': conversation_text,
                    'summary': analysis.get('summary'),
                    'importance': analysis.get('importance', 5),
                    'tags': normalized_tags,
                    'relatedTopics': analysis.get('relatedTopics', []),
                    'persona': conversation.get('persona'),
                    'conversationSnippet': conversation_snippet
                })
                
                return memory
            
            return None
        except Exception as error:
            logger.error(f'Error analyzing important moments: {error}')
            return None
    
    async def update_persona(self, session_id: str, new_persona: str) -> None:
        """
        Update persona for session
        
        Args:
            session_id: Session identifier
            new_persona: New persona type
        """
        try:
            conversations_collection = self._get_collection('conversations')
            
            conversation = await conversations_collection.find_one({'sessionId': session_id})
            if conversation:
                await conversations_collection.update_one(
                    {'sessionId': session_id},
                    {'$set': {'persona': new_persona}}
                )
            
            session_memory = self.short_term_memory.get(session_id)
            if session_memory:
                session_memory['persona'] = new_persona
            
            logger.info(f"Persona updated for session {session_id}: {new_persona}")
        except Exception as error:
            logger.error(f'Error updating persona in memory: {error}')
    
    async def get_memory_context(self, user_id: str, limit: int = 8, current_message: str = '') -> str:
        """
        Get memory context for LLM prompt. Pass current_message so relevant
        memories (e.g. "Mom's Birthday" when user asks about mom) are included.
        """
        try:
            relevant_memories = await self.get_relevant_memories(user_id, current_message or '', limit)
            if not relevant_memories:
                logger.debug(f'get_memory_context: no memories for user_id={user_id}')
                return ''
            # Prefer content over summary so exact dates/facts (e.g. "August 5th") are in the prompt
            lines = []
            for mem in relevant_memories:
                content = mem.get('content') or mem.get('summary') or ''
                if len(content) > 500:
                    content = content[:500] + '...'
                lines.append(f"- [{mem.get('title') or 'Untitled'}]: {content}")
            context = '\n'.join(lines)
            return (
                "\n\n--- RELEVANT MEMORIES (use these to answer; state the exact date or fact when it appears below) ---\n"
                + context
                + "\n--- END MEMORIES ---"
            )
        except Exception as error:
            logger.error(f'Error getting memory context: {error}')
            return ''
    
    def clear_short_term_memory(self, session_id: str) -> None:
        """
        Clear short-term memory for session
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.short_term_memory:
            del self.short_term_memory[session_id]
        logger.info(f"Short-term memory cleared for session: {session_id}")
