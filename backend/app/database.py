from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect_db(cls):
        """Connect to MongoDB Atlas."""
        try:
            cls.client = AsyncIOMotorClient(settings.mongodb_url)
            # Test connection
            await cls.client.admin.command('ping')
            logger.info("✅ Connected to MongoDB!")
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            # Don't crash - let the app start anyway
            cls.client = None
    
    @classmethod
    async def close_db(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            logger.info("🔌 MongoDB closed")
    
    @classmethod
    def get_database(cls):
        if cls.client is None:
            return None
        return cls.client[settings.database_name]
    
    @classmethod
    def get_collection(cls, collection_name: str):
        db = cls.get_database()
        if db is None:
            return None
        return db[collection_name]

def get_db():
    return Database.get_database()