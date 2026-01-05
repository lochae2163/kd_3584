"""
Clear test verified deaths data from all players in a season.

This removes the verified_deaths field from all players,
resetting them to unverified status.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
SEASON_ID = "season_6"  # Change this to your active season


async def clear_verified_deaths():
    """Remove verified_deaths field from all players in current_data."""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client["kvk_tracker"]
    current_col = db["current_data"]

    print(f"🔍 Clearing verified deaths for {SEASON_ID}...")

    # Remove verified_deaths field from all players in the season
    result = await current_col.update_one(
        {"kvk_season_id": SEASON_ID},
        {"$unset": {"players.$[].verified_deaths": ""}}
    )

    if result.modified_count > 0:
        print(f"✅ Cleared verified deaths data for {SEASON_ID}")
        print(f"   Modified {result.modified_count} document(s)")
    else:
        print(f"⚠️  No documents modified (may already be clear)")

    # Verify the change
    current_data = await current_col.find_one({"kvk_season_id": SEASON_ID})
    if current_data:
        players_with_verified = sum(
            1 for p in current_data.get('players', [])
            if 'verified_deaths' in p
        )
        total_players = len(current_data.get('players', []))
        print(f"📊 Verification status:")
        print(f"   Total players: {total_players}")
        print(f"   Players with verified deaths: {players_with_verified}")
        print(f"   Players without verified deaths: {total_players - players_with_verified}")

    client.close()
    print("✨ Done!")


if __name__ == "__main__":
    asyncio.run(clear_verified_deaths())
