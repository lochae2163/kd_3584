"""
Fix duplicate baseline entries in MongoDB

This script removes duplicate baseline entries, keeping only the most recent one.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def fix_duplicate_baselines():
    # Connect to MongoDB
    mongodb_url = os.getenv('MONGODB_URL')
    if not mongodb_url:
        print("❌ MONGODB_URL not found in environment")
        return

    client = AsyncIOMotorClient(mongodb_url)
    db = client['kvk_tracker']
    baselines_col = db['baselines']

    print("🔍 Checking for duplicate baselines...")

    # Find all baselines grouped by season_id
    pipeline = [
        {
            "$group": {
                "_id": "$kvk_season_id",
                "count": {"$sum": 1},
                "docs": {"$push": "$$ROOT"}
            }
        },
        {
            "$match": {
                "count": {"$gt": 1}
            }
        }
    ]

    duplicates = await baselines_col.aggregate(pipeline).to_list(length=None)

    if not duplicates:
        print("✅ No duplicate baselines found")
        return

    print(f"⚠️  Found {len(duplicates)} seasons with duplicate baselines")

    for dup in duplicates:
        season_id = dup['_id']
        docs = dup['docs']
        count = dup['count']

        print(f"\n📋 Season: {season_id} has {count} baselines")

        # Sort by created_at or _id (newest first)
        docs.sort(key=lambda x: x.get('created_at', x['_id']), reverse=True)

        # Keep the first (newest) one, delete the rest
        keep_doc = docs[0]
        delete_docs = docs[1:]

        print(f"   ✅ Keeping baseline: {keep_doc['_id']} (created: {keep_doc.get('created_at', 'N/A')})")

        for doc in delete_docs:
            print(f"   🗑️  Deleting baseline: {doc['_id']} (created: {doc.get('created_at', 'N/A')})")
            await baselines_col.delete_one({"_id": doc['_id']})

    print("\n✅ Cleanup complete!")

    # Now try to create the unique index
    print("\n🔧 Creating unique index on kvk_season_id...")
    try:
        # Drop existing index if it exists (without unique constraint)
        try:
            await baselines_col.drop_index("kvk_season_id_1")
            print("   🗑️  Dropped old index")
        except:
            pass

        # Create unique index
        await baselines_col.create_index("kvk_season_id", unique=True)
        print("   ✅ Created unique index on kvk_season_id")
    except Exception as e:
        print(f"   ❌ Failed to create index: {e}")

    client.close()

if __name__ == "__main__":
    asyncio.run(fix_duplicate_baselines())
