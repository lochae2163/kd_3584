"""
Migration script to backfill upload_history with player data from current_data.

This script updates existing upload_history records that don't have full player
snapshots by using the current_data as a reference.

Note: This only adds the CURRENT state to old history records. It won't give
you true historical data, but it's better than waiting for new uploads.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def migrate_history():
    """Backfill upload_history with current player data"""
    print("🚀 Starting upload_history migration...")

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
        history_collection = db["upload_history"]
        current_collection = db["current_data"]

        # Get all history records
        history_records = await history_collection.find({}).to_list(length=None)
        print(f"📊 Found {len(history_records)} upload_history records")

        # Check how many already have player data
        records_with_players = sum(1 for r in history_records if 'players' in r and r['players'])
        records_without_players = len(history_records) - records_with_players

        print(f"✅ {records_with_players} records already have player data")
        print(f"⚠️  {records_without_players} records need migration")

        if records_without_players == 0:
            print("✅ All records already migrated!")
            return

        # For each season, get the current_data and backfill
        seasons_processed = set()
        updated_count = 0

        for record in history_records:
            # Skip if already has players
            if 'players' in record and record['players']:
                continue

            kvk_season_id = record.get('kvk_season_id', 'season_1')

            # Get current data for this season (only once per season)
            if kvk_season_id not in seasons_processed:
                current = await current_collection.find_one({"kvk_season_id": kvk_season_id})

                if current and 'players' in current:
                    current_players = current['players']
                    print(f"\n📦 Processing season: {kvk_season_id}")
                    print(f"   Found {len(current_players)} players in current_data")

                    # Update ALL history records for this season that don't have players
                    result = await history_collection.update_many(
                        {
                            "kvk_season_id": kvk_season_id,
                            "$or": [
                                {"players": {"$exists": False}},
                                {"players": []}
                            ]
                        },
                        {
                            "$set": {
                                "players": current_players,
                                "migrated": True,
                                "migration_date": datetime.utcnow(),
                                "migration_note": "Backfilled with current_data (not true historical data)"
                            }
                        }
                    )

                    updated_count += result.modified_count
                    print(f"   ✅ Updated {result.modified_count} records for {kvk_season_id}")

                    seasons_processed.add(kvk_season_id)
                else:
                    print(f"   ⚠️  No current_data found for {kvk_season_id}, skipping...")

        print(f"\n🎉 Migration complete!")
        print(f"✅ Updated {updated_count} upload_history records")
        print(f"📊 Processed {len(seasons_processed)} season(s)")

        if updated_count > 0:
            print(f"\n⚠️  IMPORTANT NOTE:")
            print(f"   The migrated records contain CURRENT player data, not historical.")
            print(f"   This means all old uploads will show the same player snapshots.")
            print(f"   True historical tracking starts from the next upload onwards.")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        client.close()
        print("\n✅ Database connection closed")


if __name__ == "__main__":
    asyncio.run(migrate_history())
