"""Check what filenames are stored in the database."""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def check_filenames():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    db = client["kvk_tracker"]

    print("=" * 70)
    print("DATABASE FILENAMES CHECK")
    print("=" * 70)

    # Check baseline
    print("\n📊 BASELINE (season_6):")
    print("-" * 70)
    baselines = db["baselines"]
    baseline = await baselines.find_one({"kvk_season_id": "season_6"})
    if baseline:
        print(f"File name: {baseline.get('file_name')}")
        print(f"Timestamp: {baseline.get('timestamp')}")
        print(f"Player count: {baseline.get('player_count')}")
    else:
        print("No baseline found")

    # Check current
    print("\n📊 CURRENT DATA (season_6):")
    print("-" * 70)
    current = db["current_data"]
    current_doc = await current.find_one({"kvk_season_id": "season_6"})
    if current_doc:
        print(f"File name: {current_doc.get('file_name')}")
        print(f"Timestamp: {current_doc.get('timestamp')}")
        print(f"Description: {current_doc.get('description')}")
        print(f"Player count: {current_doc.get('player_count')}")
    else:
        print("No current data found")

    # Check history
    print("\n📊 UPLOAD HISTORY (season_6) - Last 5:")
    print("-" * 70)
    history = db["upload_history"]
    async for doc in history.find({"kvk_season_id": "season_6"}).sort("timestamp", -1).limit(5):
        print(f"\nFile: {doc.get('file_name')}")
        print(f"  Timestamp: {doc.get('timestamp')}")
        print(f"  Description: {doc.get('description', 'N/A')}")

    print("\n" + "=" * 70)
    client.close()

if __name__ == "__main__":
    asyncio.run(check_filenames())
