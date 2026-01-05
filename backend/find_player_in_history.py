"""
Search upload history to find when a player first appeared
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = "kvk_tracker"
SEASON_ID = "season_6"
PLAYER_ID = "148964283"

async def find_player_in_history():
    client = None
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DB_NAME]
        
        # Get all upload history
        history_col = db.upload_history
        uploads = await history_col.find(
            {"kvk_season_id": SEASON_ID}
        ).sort("timestamp", 1).to_list(length=100)
        
        print(f"Found {len(uploads)} uploads for {SEASON_ID}")
        print(f"Searching for player {PLAYER_ID}...\n")
        
        first_appearance = None
        
        for idx, upload in enumerate(uploads, 1):
            timestamp = upload.get('timestamp')
            desc = upload.get('description', 'No description')
            players = upload.get('players', [])
            
            # Find player in this upload
            player = next((p for p in players if p['governor_id'] == PLAYER_ID), None)
            
            if player:
                stats = player.get('stats', {})
                has_kvk_stats = any(stats.get(field, 0) > 0 for field in ['kill_points', 'deads', 't4_kills', 't5_kills'])
                
                print(f"Upload #{idx} - {timestamp}")
                print(f"  Description: {desc}")
                print(f"  Stats: power={stats.get('power'):,}, kp={stats.get('kill_points'):,}, deaths={stats.get('deads'):,}")
                print(f"  Has KvK stats: {has_kvk_stats}")
                
                if has_kvk_stats and not first_appearance:
                    first_appearance = {
                        'upload_idx': idx,
                        'timestamp': timestamp,
                        'stats': stats,
                        'description': desc
                    }
                    print(f"  ⭐ FIRST APPEARANCE WITH STATS")
                print()
            else:
                print(f"Upload #{idx} - {timestamp}: Player not found")
        
        if first_appearance:
            print(f"\n✅ Player {PLAYER_ID} first appeared in upload #{first_appearance['upload_idx']}")
            print(f"   Timestamp: {first_appearance['timestamp']}")
            print(f"   Stats: {first_appearance['stats']}")
            print(f"\n   This should be their baseline!")
        else:
            print(f"\n❌ Player {PLAYER_ID} never appeared with KvK stats in any upload")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    asyncio.run(find_player_in_history())
