# server/api/database.py
import motor.motor_asyncio
import os
from typing import Optional

client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
database = None

async def get_database():
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

async def close_database():
    """Close database connection"""
    global client
    if client:
        client.close()
        client = None