"""
Database configuration and connection management
Supports both MongoDB and file-based storage
"""

import os
from typing import Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient
from redis import asyncio as aioredis
from app.utils.logger import logger

# Global database clients
mongodb_client = None
mongodb_db = None
redis_client = None
file_db = None
db_provider = None  # 'mongodb' or 'file'


async def connect_mongodb():
    """Connect to MongoDB"""
    global mongodb_client, mongodb_db
    
    try:
        mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/eva-ai')
        mongodb_client = AsyncIOMotorClient(mongodb_uri)
        
        # Get database name from URI or use default
        db_name = mongodb_uri.split('/')[-1] or 'eva-ai'
        mongodb_db = mongodb_client[db_name]
        
        # Test connection
        await mongodb_client.admin.command('ping')
        logger.info(f"✅ Connected to MongoDB: {db_name}")
        
        return mongodb_db
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        raise


async def connect_redis():
    """Connect to Redis"""
    global redis_client
    
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        redis_password = os.getenv('REDIS_PASSWORD')
        redis_db = int(os.getenv('REDIS_DB', 0))
        
        redis_client = await aioredis.from_url(
            redis_url,
            password=redis_password if redis_password else None,
            db=redis_db,
            encoding='utf-8',
            decode_responses=True
        )
        
        # Test connection
        await redis_client.ping()
        logger.info("✅ Connected to Redis")
        
        return redis_client
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}")
        logger.warning("⚠️ Continuing without Redis (memory caching disabled)")
        redis_client = None
        return None


async def connect_file_db():
    """Connect to file-based database"""
    global file_db
    
    try:
        from app.database.file_db import connect_file_db as init_file_db
        
        data_dir = os.getenv('FILE_DB_PATH', 'data')
        file_db = await init_file_db(data_dir)
        logger.info(f"✅ Connected to file-based database: {data_dir}")
        
        return file_db
    except Exception as e:
        logger.error(f"❌ File database initialization failed: {e}")
        raise


async def connect_database():
    """Connect to the configured database provider"""
    global db_provider
    
    db_provider = os.getenv('DB_PROVIDER', 'mongodb').lower()
    
    if db_provider == 'file':
        logger.info("📁 Using file-based database")
        return await connect_file_db()
    else:
        logger.info("🍃 Using MongoDB")
        return await connect_mongodb()


async def disconnect_databases():
    """Disconnect from all databases"""
    global mongodb_client, redis_client, file_db
    
    try:
        if mongodb_client:
            mongodb_client.close()
            logger.info("✅ MongoDB disconnected")
        
        if file_db:
            from app.database.file_db import disconnect_file_db
            await disconnect_file_db()
        
        if redis_client:
            await redis_client.close()
            logger.info("✅ Redis disconnected")
    except Exception as e:
        logger.error(f"Error disconnecting databases: {e}")


def get_database():
    """Get database instance (MongoDB or File DB)"""
    if db_provider == 'file':
        return file_db
    return mongodb_db


def get_mongodb():
    """Get MongoDB database instance"""
    return mongodb_db


def get_redis():
    """Get Redis client instance"""
    return redis_client
