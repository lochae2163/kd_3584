import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

async def insert_test_data():
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.database_name]
    collection = db["snapshots"]
    
    # Test data
    test_snapshot = {
        "snapshot_id": "baseline_season_1_test",
        "kvk_season_id": "season_1",
        "fight_id": None,
        "snapshot_type": "baseline",
        "timestamp": datetime.utcnow(),
        "file_name": "test_data.csv",
        "player_count": 3,
        "processed": True,
        "players": [
            {
                "governor_id": "53242709",
                "governor_name": "ᴶᶜmasa4ん",
                "stats": {
                    "power": 230639240,
                    "kill_points": 5857666585,
                    "deads": 45368922,
                    "t4_kills": 116373863,
                    "t5_kills": 234244498
                }
            },
            {
                "governor_id": "117909431",
                "governor_name": "ˢᵖPifouPrime",
                "stats": {
                    "power": 132252619,
                    "kill_points": 2040563385,
                    "deads": 15751633,
                    "t4_kills": 80556988,
                    "t5_kills": 58679221
                }
            },
            {
                "governor_id": "46489463",
                "governor_name": "BladeCrazy",
                "stats": {
                    "power": 127517285,
                    "kill_points": 6526578201,
                    "deads": 24864060,
                    "t4_kills": 155795233,
                    "t5_kills": 245977724
                }
            }
        ]
    }
    
    # Insert
    result = await collection.insert_one(test_snapshot)
    print(f"✅ Inserted test data! ID: {result.inserted_id}")
    
    # Verify
    count = await collection.count_documents({})
    print(f"📊 Total snapshots in database: {count}")
    
    client.close()

# Run
asyncio.run(insert_test_data())