"""
Create test farm account data for testing combined leaderboard

This script:
1. Classifies a few low-ranked players as farm accounts
2. Links them to top players as their mains
3. Tests the combined leaderboard functionality
"""
import asyncio
import requests
import json

API_URL = "https://kd3584-production.up.railway.app"
SEASON_ID = "season_6"

# Test data: Let's create 3 farms and link to top 3 players
# Using real player IDs from your current data
# Pick lower contributors to simulate farm accounts
TEST_FARMS = [
    {
        "farm_id": "89666025",   # ˢᵖ Fateフェイト (rank 4, 481M KP gained)
        "main_id": "172867508",  # totoro (rank 1, 602M KP gained)
        "main_name": "トトロtotoro"
    },
    {
        "farm_id": "143414320",  # ᚱさいつよHINAちょ (rank 5, 474M KP gained)
        "main_id": "75868465",   # WA 白鳥 (rank 2, 584M KP gained)
        "main_name": "WA 白鳥"
    },
    {
        "farm_id": "51540567",   # ˢᵖShin雲TB (rank 6, 456M KP gained)
        "main_id": "148642112",  # S GxSushi (rank 3, 495M KP gained)
        "main_name": "Ｓ ＧxSushiフ"
    }
]


def classify_player(governor_id, account_type, is_dead_weight=False, notes=""):
    """Classify a player as main/farm/vacation"""
    url = f"{API_URL}/admin/players/classify"
    payload = {
        "governor_id": governor_id,
        "kvk_season_id": SEASON_ID,
        "account_type": account_type,
        "is_dead_weight": is_dead_weight,
        "classification_notes": notes
    }

    print(f"📝 Classifying {governor_id} as {account_type}...")
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"   ✅ Success: {result.get('message')}")
            return True
        else:
            print(f"   ❌ Failed: {result.get('error')}")
            return False
    else:
        print(f"   ❌ HTTP Error: {response.status_code}")
        print(f"   {response.text}")
        return False


def link_farm(farm_id, main_id):
    """Link a farm account to a main account"""
    url = f"{API_URL}/admin/players/link-farm"
    payload = {
        "farm_governor_id": farm_id,
        "main_governor_id": main_id,
        "kvk_season_id": SEASON_ID
    }

    print(f"🔗 Linking farm {farm_id} to main {main_id}...")
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"   ✅ Success: {result.get('message')}")
            return True
        else:
            print(f"   ❌ Failed: {result.get('error')}")
            return False
    else:
        print(f"   ❌ HTTP Error: {response.status_code}")
        print(f"   {response.text}")
        return False


def get_combined_leaderboard():
    """Fetch and display combined leaderboard"""
    url = f"{API_URL}/api/leaderboard/combined"
    params = {
        "kvk_season_id": SEASON_ID,
        "limit": 10
    }

    print(f"\n📊 Fetching combined leaderboard...")
    response = requests.get(url, params=params)

    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Combined Leaderboard Results:")
        print(f"   Total Players: {result.get('player_count')}")
        print(f"   Farms Merged: {result.get('total_farms_merged')}")
        print(f"\n   Top 5 Players (with farms):")
        print(f"   {'Rank':<6} {'Name':<25} {'KP Gained':<15} {'Farms':<10}")
        print(f"   {'-'*60}")

        for player in result.get('players', [])[:5]:
            rank = player.get('rank')
            name = player.get('governor_name')[:23]
            kp = player.get('combined_kill_points_gained', 0)
            farms = player.get('farm_count', 0)

            print(f"   {rank:<6} {name:<25} {kp:>13,} {farms:>8}")

            # Show farm details if any
            if player.get('farm_details'):
                for farm in player['farm_details']:
                    farm_name = farm['governor_name'][:20]
                    farm_kp = farm['kill_points_gained']
                    print(f"          └─ 🌾 {farm_name:<20} +{farm_kp:>10,} KP")

        return result
    else:
        print(f"   ❌ HTTP Error: {response.status_code}")
        print(f"   {response.text}")
        return None


def main():
    """Run the test data creation"""
    print("=" * 70)
    print("🧪 Creating Test Farm Account Data")
    print("=" * 70)
    print(f"\nSeason: {SEASON_ID}")
    print(f"Test Farms: {len(TEST_FARMS)}")
    print()

    # Step 1: Classify farms
    print("STEP 1: Classifying players as farm accounts")
    print("-" * 70)
    for test in TEST_FARMS:
        classify_player(
            test["farm_id"],
            "farm",
            notes=f"Test farm for {test['main_name']}"
        )

    print()

    # Step 2: Link farms to mains
    print("STEP 2: Linking farms to main accounts")
    print("-" * 70)
    for test in TEST_FARMS:
        link_farm(test["farm_id"], test["main_id"])

    print()

    # Step 3: Test combined leaderboard
    print("STEP 3: Testing combined leaderboard")
    print("-" * 70)
    result = get_combined_leaderboard()

    print()
    print("=" * 70)
    print("✅ Test Data Creation Complete!")
    print("=" * 70)
    print()
    print("You can now:")
    print("1. View combined leaderboard at /api/leaderboard/combined")
    print("2. Check admin panel to see farm classifications")
    print("3. Test unlinking farms")
    print()


if __name__ == "__main__":
    main()
