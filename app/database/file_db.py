"""
File-based database implementation using JSON files
Simple alternative to MongoDB for local development
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiofiles
from app.utils.logger import logger


def serialize_datetime(obj: Any) -> Any:
    """Convert datetime objects to ISO format strings recursively"""
    if isinstance(obj, datetime):
        iso_str = obj.isoformat()
        return iso_str + 'Z' if not iso_str.endswith('Z') else iso_str
    elif isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    return obj


def ensure_json_serializable(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all data is JSON serializable before saving"""
    try:
        # Try to serialize and deserialize to catch any issues
        json_str = json.dumps(data, default=str)
        return json.loads(json_str)
    except Exception:
        # Fallback to recursive serialization
        return serialize_datetime(data)


class FileDatabase:
    """File-based database using JSON files"""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize file database
        
        Args:
            data_dir: Directory to store database files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Create collection directories
        self.conversations_dir = self.data_dir / "conversations"
        self.memories_dir = self.data_dir / "memories"
        
        self.conversations_dir.mkdir(exist_ok=True)
        self.memories_dir.mkdir(exist_ok=True)
        
        # In-memory cache for faster access
        self._cache: Dict[str, Dict[str, Any]] = {
            'conversations': {},
            'memories': {}
        }
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        
        logger.info(f"✅ File-based database initialized at: {self.data_dir}")
    
    async def load_cache(self):
        """Load all data into memory cache"""
        async with self._lock:
            # Load conversations
            for file_path in self.conversations_dir.glob("*.json"):
                try:
                    async with aiofiles.open(file_path, 'r') as f:
                        content = await f.read()
                        data = json.loads(content)
                        self._cache['conversations'][data['sessionId']] = data
                except Exception as e:
                    logger.error(f"Error loading conversation {file_path}: {e}")
            
            # Load memories
            for file_path in self.memories_dir.glob("*.json"):
                try:
                    async with aiofiles.open(file_path, 'r') as f:
                        content = await f.read()
                        data = json.loads(content)
                        memory_id = file_path.stem
                        self._cache['memories'][memory_id] = data
                except Exception as e:
                    logger.error(f"Error loading memory {file_path}: {e}")
            
            logger.info(f"Loaded {len(self._cache['conversations'])} conversations and {len(self._cache['memories'])} memories")
    
    # Conversation methods
    
    async def find_conversation(self, query: Dict[str, Any], sort: List[tuple] = None) -> Optional[Dict[str, Any]]:
        """Find a single conversation matching the query"""
        session_id = query.get('sessionId')
        if session_id and session_id in self._cache['conversations']:
            return serialize_datetime(self._cache['conversations'][session_id].copy())
        
        # If no direct session_id match, search all conversations
        results = []
        for conv in self._cache['conversations'].values():
            match = True
            for key, value in query.items():
                if not self._match_field(conv, key, value):
                    match = False
                    break
            if match:
                results.append(conv.copy())
        
        if not results:
            return None
        
        # Sort if specified
        if sort:
            for field, direction in reversed(sort):
                reverse = (direction == -1)
                results.sort(key=lambda x: x.get(field, ''), reverse=reverse)
        
        return serialize_datetime(results[0]) if results else None
    
    async def find_conversations(self, query: Dict[str, Any] = None, sort: List[tuple] = None, limit: int = 0, projection: Dict[str, int] = None) -> List[Dict[str, Any]]:
        """Find multiple conversations matching the query"""
        if query is None:
            query = {}
        
        results = []
        
        # Filter by query
        for conv in self._cache['conversations'].values():
            match = True
            for key, value in query.items():
                # Handle MongoDB operators
                if key == "messages.0":
                    # Check if first message exists
                    if isinstance(value, dict) and "$exists" in value:
                        has_messages = len(conv.get("messages", [])) > 0
                        if value["$exists"] != has_messages:
                            match = False
                            break
                elif key == "$or":
                    # Handle $or operator
                    or_match = False
                    for or_condition in value:
                        or_condition_match = True
                        for or_key, or_value in or_condition.items():
                            if not self._match_field(conv, or_key, or_value):
                                or_condition_match = False
                                break
                        if or_condition_match:
                            or_match = True
                            break
                    if not or_match:
                        match = False
                        break
                elif not self._match_field(conv, key, value):
                    match = False
                    break
            
            if match:
                # Apply projection if specified
                if projection:
                    filtered_conv = {}
                    for field, include in projection.items():
                        if include and field in conv:
                            filtered_conv[field] = conv[field]
                    results.append(serialize_datetime(filtered_conv))
                else:
                    results.append(serialize_datetime(conv.copy()))
        
        # Sort results
        if sort:
            for field, direction in reversed(sort):
                reverse = (direction == -1)
                results.sort(key=lambda x: x.get(field, ''), reverse=reverse)
        
        # Limit results
        if limit > 0:
            results = results[:limit]
        
        return results
    
    def _match_field(self, doc: Dict[str, Any], key: str, value: Any) -> bool:
        """Check if a field matches the query value"""
        if key not in doc:
            return False
        
        doc_value = doc[key]
        
        # Handle MongoDB operators
        if isinstance(value, dict):
            if "$regex" in value:
                # Simple regex match (case-insensitive if $options: "i")
                import re
                pattern = value["$regex"]
                flags = re.IGNORECASE if value.get("$options") == "i" else 0
                
                # Handle nested field searches (e.g., messages.content)
                if "." in key:
                    parts = key.split(".")
                    nested_value = doc
                    for part in parts:
                        if isinstance(nested_value, dict):
                            nested_value = nested_value.get(part)
                        elif isinstance(nested_value, list):
                            # Search in list items
                            for item in nested_value:
                                if isinstance(item, dict) and part in item:
                                    if re.search(pattern, str(item[part]), flags):
                                        return True
                            return False
                        else:
                            return False
                    return bool(re.search(pattern, str(nested_value), flags))
                else:
                    return bool(re.search(pattern, str(doc_value), flags))
        
        return doc_value == value
    
    async def insert_conversation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new conversation"""
        async with self._lock:
            session_id = data['sessionId']
            
            # Ensure all data is JSON serializable
            data = ensure_json_serializable(data)
            
            # Add timestamps if not present
            now = datetime.utcnow().isoformat() + 'Z'
            data['createdAt'] = data.get('createdAt', now)
            data['updatedAt'] = data.get('updatedAt', now)
            data['lastMessageAt'] = data.get('lastMessageAt', now)
            
            # Save to cache
            self._cache['conversations'][session_id] = data
            
            # Save to file
            file_path = self.conversations_dir / f"{session_id}.json"
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(json.dumps(data, indent=2))
            
            return data
    
    async def update_conversation(self, session_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a conversation"""
        async with self._lock:
            if session_id not in self._cache['conversations']:
                return None
            
            # Ensure update data is JSON serializable
            update_data = ensure_json_serializable(update_data)
            
            # Update cache
            conversation = self._cache['conversations'][session_id]
            conversation.update(update_data)
            conversation['updatedAt'] = datetime.utcnow().isoformat() + 'Z'
            
            # Save to file
            file_path = self.conversations_dir / f"{session_id}.json"
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(json.dumps(conversation, indent=2))
            
            return conversation
    
    async def delete_conversation(self, session_id: str) -> bool:
        """Delete a conversation"""
        async with self._lock:
            if session_id not in self._cache['conversations']:
                return False
            
            # Remove from cache
            del self._cache['conversations'][session_id]
            
            # Delete file
            file_path = self.conversations_dir / f"{session_id}.json"
            if file_path.exists():
                file_path.unlink()
            
            return True
    
    # Memory methods
    
    async def find_memory(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single memory matching the query"""
        memory_id = query.get('_id')
        if memory_id and memory_id in self._cache['memories']:
            return serialize_datetime(self._cache['memories'][memory_id].copy())
        
        # Search by other fields
        for memory in self._cache['memories'].values():
            match = True
            for key, value in query.items():
                if key not in memory or memory[key] != value:
                    match = False
                    break
            if match:
                return serialize_datetime(memory.copy())
        
        return None
    
    async def find_memories(self, query: Dict[str, Any] = None, sort: List[tuple] = None, limit: int = 0) -> List[Dict[str, Any]]:
        """Find multiple memories matching the query"""
        if query is None:
            query = {}
        
        results = []
        
        # Filter by query
        for memory in self._cache['memories'].values():
            match = True
            for key, value in query.items():
                if key not in memory or memory[key] != value:
                    match = False
                    break
            if match:
                results.append(serialize_datetime(memory.copy()))
        
        # Sort results
        if sort:
            for field, direction in reversed(sort):
                reverse = (direction == -1)
                results.sort(key=lambda x: x.get(field, ''), reverse=reverse)
        
        # Limit results
        if limit > 0:
            results = results[:limit]
        
        return results
    
    async def insert_memory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new memory"""
        async with self._lock:
            # Generate ID
            memory_id = f"{data['sessionId']}_{int(datetime.utcnow().timestamp() * 1000)}"
            data['_id'] = memory_id
            
            # Ensure all data is JSON serializable
            data = ensure_json_serializable(data)
            
            # Add timestamps if not present
            now = datetime.utcnow().isoformat() + 'Z'
            if 'metadata' not in data:
                data['metadata'] = {}
            data['metadata']['createdAt'] = data['metadata'].get('createdAt', now)
            data['metadata']['updatedAt'] = data['metadata'].get('updatedAt', now)
            
            # Save to cache
            self._cache['memories'][memory_id] = data
            
            # Save to file
            file_path = self.memories_dir / f"{memory_id}.json"
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(json.dumps(data, indent=2))
            
            return data
    
    async def update_memory(self, memory_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a memory"""
        async with self._lock:
            if memory_id not in self._cache['memories']:
                return None
            
            # Ensure update data is JSON serializable
            update_data = ensure_json_serializable(update_data)
            
            # Update cache
            memory = self._cache['memories'][memory_id]
            memory.update(update_data)
            
            if 'metadata' not in memory:
                memory['metadata'] = {}
            memory['metadata']['updatedAt'] = datetime.utcnow().isoformat() + 'Z'
            
            # Save to file
            file_path = self.memories_dir / f"{memory_id}.json"
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(json.dumps(memory, indent=2))
            
            return memory
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory"""
        async with self._lock:
            if memory_id not in self._cache['memories']:
                return False
            
            # Remove from cache
            del self._cache['memories'][memory_id]
            
            # Delete file
            file_path = self.memories_dir / f"{memory_id}.json"
            if file_path.exists():
                file_path.unlink()
            
            return True
    
    async def count_documents(self, collection: str, query: Dict[str, Any] = None) -> int:
        """Count documents in a collection"""
        if query is None:
            query = {}
        
        cache_key = collection + 's'  # conversations or memories
        if cache_key not in self._cache:
            return 0
        
        count = 0
        for doc in self._cache[cache_key].values():
            match = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    match = False
                    break
            if match:
                count += 1
        
        return count
    
    def get_collection(self, name: str):
        """Get a collection (returns self for compatibility)"""
        return FileCollection(self, name)


class FileCollection:
    """File collection wrapper for MongoDB-like API"""
    
    def __init__(self, db: FileDatabase, name: str):
        self.db = db
        self.name = name
    
    async def find_one(self, query: Dict[str, Any], sort: List[tuple] = None) -> Optional[Dict[str, Any]]:
        """Find one document"""
        if self.name == 'conversations':
            return await self.db.find_conversation(query, sort)
        elif self.name == 'memories':
            return await self.db.find_memory(query)
        return None
    
    def find(self, query: Dict[str, Any] = None, projection: Dict[str, int] = None) -> 'FileCursor':
        """Find multiple documents (returns cursor, not awaitable)"""
        return FileCursor(self.db, self.name, query or {}, projection)
    
    async def insert_one(self, data: Dict[str, Any]) -> 'FileInsertResult':
        """Insert one document"""
        if self.name == 'conversations':
            result = await self.db.insert_conversation(data)
        elif self.name == 'memories':
            result = await self.db.insert_memory(data)
        else:
            result = None
        
        return FileInsertResult(result)
    
    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any]) -> 'FileUpdateResult':
        """Update one document"""
        # Extract the actual update data from $set operator
        update_data = update.get('$set', update)
        
        if self.name == 'conversations':
            session_id = query.get('sessionId')
            result = await self.db.update_conversation(session_id, update_data)
        elif self.name == 'memories':
            memory_id = query.get('_id')
            result = await self.db.update_memory(memory_id, update_data)
        else:
            result = None
        
        return FileUpdateResult(result is not None)
    
    async def delete_one(self, query: Dict[str, Any]) -> 'FileDeleteResult':
        """Delete one document"""
        if self.name == 'conversations':
            session_id = query.get('sessionId')
            success = await self.db.delete_conversation(session_id)
        elif self.name == 'memories':
            memory_id = query.get('_id')
            success = await self.db.delete_memory(memory_id)
        else:
            success = False
        
        return FileDeleteResult(1 if success else 0)
    
    async def count_documents(self, query: Dict[str, Any] = None) -> int:
        """Count documents"""
        return await self.db.count_documents(self.name, query or {})


class FileCursor:
    """Cursor for iterating over query results"""
    
    def __init__(self, db: FileDatabase, collection: str, query: Dict[str, Any], projection: Dict[str, int] = None):
        self.db = db
        self.collection = collection
        self.query = query
        self.projection = projection
        self._sort = None
        self._limit = 0
    
    def sort(self, field: str, direction: int = 1):
        """Set sort order"""
        if self._sort is None:
            self._sort = []
        self._sort.append((field, direction))
        return self
    
    def limit(self, limit: int):
        """Set result limit"""
        self._limit = limit
        return self
    
    async def to_list(self, length: Optional[int] = None) -> List[Dict[str, Any]]:
        """Convert cursor to list"""
        if self.collection == 'conversations':
            results = await self.db.find_conversations(self.query, self._sort, self._limit or length or 0, self.projection)
        elif self.collection == 'memories':
            results = await self.db.find_memories(self.query, self._sort, self._limit or length or 0)
        else:
            results = []
        
        return results


class FileInsertResult:
    """Result of insert operation"""
    
    def __init__(self, document: Optional[Dict[str, Any]]):
        self.inserted_id = document.get('_id') if document else None
        self.acknowledged = document is not None


class FileUpdateResult:
    """Result of update operation"""
    
    def __init__(self, success: bool):
        self.modified_count = 1 if success else 0
        self.acknowledged = success


class FileDeleteResult:
    """Result of delete operation"""
    
    def __init__(self, count: int):
        self.deleted_count = count
        self.acknowledged = count > 0


# Global file database instance
file_db: Optional[FileDatabase] = None


async def connect_file_db(data_dir: str = "data") -> FileDatabase:
    """Connect to file-based database"""
    global file_db
    
    try:
        file_db = FileDatabase(data_dir)
        await file_db.load_cache()
        logger.info(f"✅ File-based database ready: {data_dir}")
        return file_db
    except Exception as e:
        logger.error(f"❌ File database initialization failed: {e}")
        raise


async def disconnect_file_db():
    """Disconnect from file database (no-op for file-based)"""
    global file_db
    if file_db:
        logger.info("✅ File database closed")
        file_db = None


def get_file_db() -> Optional[FileDatabase]:
    """Get file database instance"""
    return file_db
