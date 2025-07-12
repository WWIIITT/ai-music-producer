# server/api/database.py
import os
from typing import Optional, Any
import motor.motor_asyncio

# Use Any type to avoid Pylance issues
client: Optional[Any] = None
database: Optional[Any] = None

async def get_database() -> Any:
    """Get MongoDB database instance"""
    global client, database
    
    if database is None:
        mongo_url = os.getenv("MONGO_URL", "mongodb://admin:password123@localhost:27017/")
        database_name = os.getenv("DATABASE_NAME", "music_producer")
        
        client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
        database = client[database_name]
        
        # Create indexes
        await database.beats.create_index("created_at")
        await database.projects.create_index("created_at")
        await database.melodies.create_index("created_at")
    
    return database

async def close_database() -> None:
    """Close database connection"""
    global client, database
    if client:
        client.close()
        client = None
        database = None