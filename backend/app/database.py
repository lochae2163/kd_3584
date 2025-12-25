from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    """
    Database connection manager.
    Uses Motor (async MongoDB driver) for FastAPI compatibility.
    """
    
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect_db(cls):
        """Connect to MongoDB Atlas."""
        try:
            cls.client = AsyncIOMotorClient(settings.mongodb_url)
            # Test connection
            await cls.client.admin.command('ping')
            logger.info("✅ Successfully connected to MongoDB Atlas!")
        except ConnectionFailure as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def close_db(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            logger.info("🔌 MongoDB connection closed")
    
    @classmethod
    def get_database(cls):
        """Get database instance."""
        return cls.client[settings.database_name]
    
    @classmethod
    def get_collection(cls, collection_name: str):
        """Get specific collection."""
        return cls.get_database()[collection_name]

# Convenience function
def get_db():
    """Dependency for route handlers."""
    return Database.get_database()