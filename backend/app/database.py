from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging
import certifi

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect_db(cls):
        """Connect to MongoDB Atlas."""
        try:
            cls.client = AsyncIOMotorClient(
                settings.mongodb_url,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=5000
            )
            # Test connection
            await cls.client.admin.command('ping')
            logger.info("✅ Connected to MongoDB!")

            # Initialize database indexes for performance
            await cls.ensure_indexes()

        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            # Don't crash - let the app start anyway
            cls.client = None

    @classmethod
    async def ensure_indexes(cls):
        """
        Create database indexes for optimal query performance.

        Indexes dramatically improve query performance by transforming
        O(n) collection scans into O(log n) indexed lookups.
        """
        if cls.client is None:
            logger.warning("⚠️  Cannot create indexes: No database connection")
            return

        try:
            db = cls.get_database()

            # ========================================
            # 1. kvk_seasons Collection
            # ========================================
            seasons_col = db["kvk_seasons"]

            # Index for finding specific season by ID (most common query)
            await seasons_col.create_index("season_id", unique=True)

            # Index for finding active season
            await seasons_col.create_index("is_active")

            # Index for sorting by season number (used in admin panel)
            await seasons_col.create_index([("season_number", -1)])

            # Compound index for status queries
            await seasons_col.create_index([("is_archived", 1), ("is_active", 1)])

            logger.info("✅ Created indexes for kvk_seasons collection")

            # ========================================
            # 2. current_data Collection
            # ========================================
            current_col = db["current_data"]

            # Index for finding current data by season
            await current_col.create_index("kvk_season_id", unique=True)

            # Index for timestamp (used in history tracking)
            await current_col.create_index([("timestamp", -1)])

            logger.info("✅ Created indexes for current_data collection")

            # ========================================
            # 3. baselines Collection
            # ========================================
            baselines_col = db["baselines"]

            # Index for finding baseline by season
            try:
                await baselines_col.create_index("kvk_season_id", unique=True)
            except Exception as e:
                if "duplicate key" in str(e).lower():
                    logger.warning(f"⚠️  Cannot create unique index on baselines.kvk_season_id - duplicate entries exist")
                    logger.warning(f"⚠️  Run: python -m app.scripts.fix_duplicate_baselines to fix this issue")
                else:
                    raise

            # Index for timestamp
            await baselines_col.create_index([("timestamp", -1)])

            logger.info("✅ Created indexes for baselines collection")

            # ========================================
            # 4. upload_history Collection
            # ========================================
            history_col = db["upload_history"]

            # Compound index for season + timestamp queries
            await history_col.create_index([("kvk_season_id", 1), ("timestamp", -1)])

            # Index for upload type filtering
            await history_col.create_index("upload_type")

            logger.info("✅ Created indexes for upload_history collection")

            # ========================================
            # 5. player_classifications Collection
            # ========================================
            classifications_col = db["player_classifications"]

            # Index for finding classification by season
            await classifications_col.create_index("kvk_season_id", unique=True)

            logger.info("✅ Created indexes for player_classifications collection")

            # ========================================
            # 6. verified_deaths Collection
            # ========================================
            deaths_col = db["verified_deaths"]

            # Compound index for season + governor queries
            await deaths_col.create_index([("kvk_season_id", 1), ("governor_id", 1)])

            # Index for verification status filtering
            await deaths_col.create_index("is_verified")

            logger.info("✅ Created indexes for verified_deaths collection")

            logger.info("🚀 All database indexes created successfully!")

        except Exception as e:
            logger.error(f"❌ Failed to create indexes: {e}", exc_info=True)
            # Don't crash - indexes are performance optimization, not critical

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