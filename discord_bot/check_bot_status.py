#!/usr/bin/env python3
"""
Quick script to check if the Discord bot and API are working
Run this to verify everything is online
"""

import requests
import os
from datetime import datetime

API_URL = os.getenv('API_URL', 'https://kd3584-production.up.railway.app')
KVK_SEASON_ID = os.getenv('KVK_SEASON_ID', 'season_1')

def check_api():
    """Check if API is responding"""
    print("🔍 Checking API status...")
    try:
        response = requests.get(f"{API_URL}/", timeout=10)
        if response.status_code == 200 or response.status_code == 405:
            print("✅ API is online")
            return True
        else:
            print(f"⚠️  API returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API is offline: {e}")
        return False

def check_api_data():
    """Check if API has data"""
    print(f"\n🔍 Checking KvK data for {KVK_SEASON_ID}...")
    try:
        response = requests.get(
            f"{API_URL}/api/stats/summary?kvk_season_id={KVK_SEASON_ID}",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            player_count = data.get('player_count', 0)
            baseline_date = data.get('baseline_date', 'N/A')
            current_date = data.get('current_date', 'N/A')

            print(f"✅ Data available:")
            print(f"   Players: {player_count}")
            print(f"   Baseline: {baseline_date}")
            print(f"   Current: {current_date}")
            return True
        else:
            print(f"⚠️  API returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to fetch data: {e}")
        return False

def check_leaderboard():
    """Check if leaderboard endpoint works"""
    print(f"\n🔍 Checking leaderboard endpoint...")
    try:
        response = requests.get(
            f"{API_URL}/api/leaderboard?kvk_season_id={KVK_SEASON_ID}&sort_by=kill_points_gained&limit=5",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            leaderboard = data.get('leaderboard', [])
            print(f"✅ Leaderboard working: {len(leaderboard)} players returned")
            if leaderboard:
                top_player = leaderboard[0]
                print(f"   Top player: {top_player.get('governor_name')} (Rank #{top_player.get('rank')})")
            return True
        else:
            print(f"⚠️  Leaderboard returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to fetch leaderboard: {e}")
        return False

def main():
    print("=" * 60)
    print("Kingdom 3584 KvK Tracker - System Status Check")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API URL: {API_URL}")
    print(f"Season: {KVK_SEASON_ID}")
    print("=" * 60)

    # Check all systems
    api_ok = check_api()
    data_ok = check_api_data()
    leaderboard_ok = check_leaderboard()

    print("\n" + "=" * 60)
    print("📊 Summary:")
    print("=" * 60)
    print(f"API Online:        {'✅ Yes' if api_ok else '❌ No'}")
    print(f"Data Available:    {'✅ Yes' if data_ok else '❌ No'}")
    print(f"Leaderboard Works: {'✅ Yes' if leaderboard_ok else '❌ No'}")

    if api_ok and data_ok and leaderboard_ok:
        print("\n🎉 All systems operational!")
        print("\n✅ Your Discord bot should be working perfectly!")
        print("\nNext steps:")
        print("1. Check bot is online in Discord (green circle)")
        print("2. Try command: /stats YOUR_GOVERNOR_ID")
        print("3. Try command: /top kill_points_gained 10")
        print("4. Try command: /summary")
    else:
        print("\n⚠️  Some systems have issues!")
        print("\nTroubleshooting:")
        if not api_ok:
            print("- Check if Railway backend is running")
            print("- Verify API_URL is correct")
        if not data_ok:
            print("- Upload baseline data in admin panel")
            print("- Check KVK_SEASON_ID matches uploaded data")
        if not leaderboard_ok:
            print("- Check API logs in Railway")
            print("- Verify MongoDB connection")

    print("=" * 60)

if __name__ == "__main__":
    main()
