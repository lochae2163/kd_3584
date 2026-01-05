"""
Initialize Season 6 as the current active season

Run this script once to set up season_6 in the database
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def initialize_season_6():
    """Initialize season_6 as the active season"""
    print("🚀 Initializing Season 6...")

    # Get MongoDB connection string from environment
    mongodb_url = os.getenv("MONGODB_URL")
    database_name = os.getenv("DATABASE_NAME", "kvk_tracker")

    if not mongodb_url:
        print("❌ MONGODB_URL not found in environment variables!")
        return

    # Connect to database directly
    client = AsyncIOMotorClient(mongodb_url)
    db = client[database_name]

    try:
        seasons_col = db["kvk_seasons"]

        # Check if season_6 already exists
        existing = await seasons_col.find_one({"season_id": "season_6"})
        if existing:
            print("⚠️  Season 6 already exists!")
            print(f"   Status: {existing.get('status')}")
            print(f"   Is Active: {existing.get('is_active')}")
            print(f"   Is Archived: {existing.get('is_archived')}")

            # Ask if we should activate it
            print("\n   Activating season_6...")
        else:
            # Create season_6
            print("📝 Creating season_6...")

        # Deactivate all other seasons
        await seasons_col.update_many(
            {},
            {"$set": {"is_active": False}}
        )

        # Create or update season_6
        season_6 = {
            "season_id": "season_6",
            "season_name": "KvK 6 - Kingdom 3584",
            "season_number": 6,
            "status": "active",
            "is_active": True,
            "is_archived": False,
            "start_date": datetime(2026, 1, 1),
            "end_date": None,
            "created_at": datetime.utcnow(),
            "activated_at": datetime.utcnow(),
            "completed_at": None,
            "archived_at": None,
            "has_baseline": False,
            "has_current_data": False,
            "final_data_uploaded": False,
            "description": "Kingdom 3584 - KvK Season 6",
            "kingdom_id": "3584",
            "enemy_kingdoms": [],
            "total_uploads": 0,
            "player_count": 0
        }

        # Upsert season_6
        result = await seasons_col.update_one(
            {"season_id": "season_6"},
            {"$set": season_6},
            upsert=True
        )

        if result.upserted_id:
            print("✅ Season 6 created successfully!")
        else:
            print("✅ Season 6 updated successfully!")

        # Check if we have existing data for season_6
        baseline_col = db["baselines"]
        current_col = db["current_data"]
        history_col = db["upload_history"]

        baseline_count = await baseline_col.count_documents({"kvk_season_id": "season_6"})
        current_count = await current_col.count_documents({"kvk_season_id": "season_6"})
        history_count = await history_col.count_documents({"kvk_season_id": "season_6"})

        print(f"\n📊 Season 6 Data Status:")
        print(f"   Baseline: {'✅ Exists' if baseline_count > 0 else '❌ Not uploaded'}")
        print(f"   Current Data: {'✅ Exists' if current_count > 0 else '❌ Not uploaded'}")
        print(f"   Upload History: {history_count} uploads")

        if baseline_count > 0:
            baseline = await baseline_col.find_one({"kvk_season_id": "season_6"})
            player_count = baseline.get('player_count', 0)

            # Update season with actual stats
            await seasons_col.update_one(
                {"season_id": "season_6"},
                {
                    "$set": {
                        "has_baseline": True,
                        "has_current_data": current_count > 0,
                        "total_uploads": history_count,
                        "player_count": player_count
                    }
                }
            )
            print(f"   Players: {player_count}")

        print("\n🎉 Season 6 is now ACTIVE!")
        print("   All future uploads will go to season_6")
        print("   You can now use the API with kvk_season_id=season_6")

        # Migrate season_1 data if it exists and season_6 is empty
        if baseline_count == 0:
            print("\n🔍 Checking for season_1 data to migrate...")
            season_1_baseline = await baseline_col.find_one({"kvk_season_id": "season_1"})

            if season_1_baseline:
                print("   Found season_1 data!")
                print("   You can either:")
                print("   1. Re-upload your KvK 6 baseline to season_6")
                print("   2. Continue using existing data (if it's KvK 6)")
                print("\n   Note: Season 1 data remains unchanged and separate")

    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        client.close()
        print("\n✅ Database connection closed")


if __name__ == "__main__":
    asyncio.run(initialize_season_6())
