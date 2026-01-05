"""
Create Excel template for verified deaths upload

This script creates:
1. Empty template file for admins to fill in
2. Sample test data file with real player IDs
"""
import pandas as pd
import requests

API_URL = "https://kd3584-production.up.railway.app"
SEASON_ID = "season_6"


def create_empty_template():
    """Create empty Excel template."""
    template_data = {
        'governor_id': ['Example: 172867508', 'Example: 75868465'],
        't4_deaths': [0, 0],
        't5_deaths': [0, 0],
        'notes': ['Optional admin notes', '']
    }

    df = pd.DataFrame(template_data)
    filename = 'verified_deaths_template.xlsx'

    # Create Excel with formatting
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Verified Deaths')

        # Get worksheet
        worksheet = writer.sheets['Verified Deaths']

        # Set column widths
        worksheet.column_dimensions['A'].width = 20  # governor_id
        worksheet.column_dimensions['B'].width = 15  # t4_deaths
        worksheet.column_dimensions['C'].width = 15  # t5_deaths
        worksheet.column_dimensions['D'].width = 30  # notes

    print(f"✅ Created empty template: {filename}")
    return filename


def create_test_data():
    """Create test data using top 10 players from current season."""
    print(f"📊 Fetching top 10 players from {SEASON_ID}...")

    response = requests.get(
        f"{API_URL}/api/leaderboard",
        params={"kvk_season_id": SEASON_ID, "limit": 10}
    )

    if response.status_code != 200:
        print(f"❌ Failed to fetch players: {response.status_code}")
        return None

    data = response.json()
    players = data.get('leaderboard', [])

    if not players:
        print("❌ No players found")
        return None

    print(f"✅ Found {len(players)} players")

    # Create test data with estimated T4/T5 death breakdown
    test_data = []

    for player in players:
        gov_id = player['governor_id']
        gov_name = player['governor_name']
        total_deaths = player['stats']['deads']

        # Estimate 60% T4, 40% T5 split
        estimated_t4_deaths = int(total_deaths * 0.6)
        estimated_t5_deaths = total_deaths - estimated_t4_deaths

        test_data.append({
            'governor_id': gov_id,
            't4_deaths': estimated_t4_deaths,
            't5_deaths': estimated_t5_deaths,
            'notes': f"Estimated from {total_deaths:,} total deaths"
        })

        print(f"  {gov_name}: T4={estimated_t4_deaths:,}, T5={estimated_t5_deaths:,}")

    # Create DataFrame
    df = pd.DataFrame(test_data)
    filename = f'verified_deaths_test_{SEASON_ID}.xlsx'

    # Save to Excel
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Verified Deaths')

        # Get worksheet
        worksheet = writer.sheets['Verified Deaths']

        # Set column widths
        worksheet.column_dimensions['A'].width = 20  # governor_id
        worksheet.column_dimensions['B'].width = 15  # t4_deaths
        worksheet.column_dimensions['C'].width = 15  # t5_deaths
        worksheet.column_dimensions['D'].width = 40  # notes

    print(f"✅ Created test data file: {filename}")
    return filename


def main():
    print("=" * 70)
    print("📁 Creating Verified Deaths Excel Templates")
    print("=" * 70)
    print()

    # Create empty template
    print("STEP 1: Creating empty template for admins")
    print("-" * 70)
    template_file = create_empty_template()
    print()

    # Create test data
    print("STEP 2: Creating test data from current season")
    print("-" * 70)
    test_file = create_test_data()
    print()

    print("=" * 70)
    print("✅ Templates Created Successfully!")
    print("=" * 70)
    print()
    print("Files created:")
    print(f"  1. {template_file} - Empty template for admins to fill")
    print(f"  2. {test_file} - Test data with top 10 players")
    print()
    print("Usage:")
    print(f"  1. Admins can use the template to manually enter verified deaths")
    print(f"  2. Test the upload endpoint with: {test_file}")
    print()


if __name__ == "__main__":
    main()
