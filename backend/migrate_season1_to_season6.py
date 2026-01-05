"""
Migrate all season_1 data to season_6

This script moves all data from season_1 to season_6:
- Baselines
- Current data
- Upload history
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def migrate_season_data():
    """Migrate all season_1 data to season_6"""
    print("🔄 Starting migration from season_1 to season_6...")

    # Get MongoDB connection string from environment
    mongodb_url = os.getenv("MONGODB_URL")
    database_name = os.getenv("DATABASE_NAME", "kvk_tracker")

    if not mongodb_url:
        print("❌ MONGODB_URL not found in environment variables!")
        return

    # Connect to database
    client = AsyncIOMotorClient(mongodb_url)
    db = client[database_name]

    try:
        # Collections to migrate
        collections_to_migrate = ["baselines", "current_data", "upload_history"]

        for collection_name in collections_to_migrate:
            print(f"\n📦 Migrating {collection_name}...")
            collection = db[collection_name]

            # Count documents with season_1
            season_1_count = await collection.count_documents({"kvk_season_id": "season_1"})
            print(f"   Found {season_1_count} documents with season_1")

            if season_1_count == 0:
                print(f"   ✅ No documents to migrate in {collection_name}")
                continue

            # Update all season_1 to season_6
            result = await collection.update_many(
                {"kvk_season_id": "season_1"},
                {"$set": {"kvk_season_id": "season_6"}}
            )

            print(f"   ✅ Updated {result.modified_count} documents to season_6")

        # Update season_6 stats
        print("\n📊 Updating season_6 statistics...")

        baseline_col = db["baselines"]
        baseline = await baseline_col.find_one({"kvk_season_id": "season_6"})

        history_col = db["upload_history"]
        upload_count = await history_col.count_documents({"kvk_season_id": "season_6"})

        current_col = db["current_data"]
        current = await current_col.find_one({"kvk_season_id": "season_6"})

        seasons_col = db["kvk_seasons"]
        await seasons_col.update_one(
            {"season_id": "season_6"},
            {
                "$set": {
                    "has_baseline": baseline is not None,
                    "has_current_data": current is not None,
                    "total_uploads": upload_count,
                    "player_count": baseline.get('player_count', 0) if baseline else 0
                }
            }
        )

        print(f"   ✅ Season 6 stats updated:")
        print(f"      - Has baseline: {baseline is not None}")
        print(f"      - Has current data: {current is not None}")
        print(f"      - Total uploads: {upload_count}")
        print(f"      - Player count: {baseline.get('player_count', 0) if baseline else 0}")

        # Check if season_1 still has any data
        print("\n🔍 Checking remaining season_1 data...")
        for collection_name in collections_to_migrate:
            collection = db[collection_name]
            remaining = await collection.count_documents({"kvk_season_id": "season_1"})
            if remaining > 0:
                print(f"   ⚠️  {collection_name} still has {remaining} season_1 documents")
            else:
                print(f"   ✅ {collection_name} has no season_1 documents")

        print("\n🎉 Migration complete!")
        print("   All season_1 data has been moved to season_6")
        print("   You can now safely delete the season_1 entry from kvk_seasons")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        client.close()
        print("\n✅ Database connection closed")


if __name__ == "__main__":
    asyncio.run(migrate_season_data())
