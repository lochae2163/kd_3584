"""
Create Excel template for final KvK data upload

This script creates an Excel template pre-filled with all current players.
Admins just need to:
1. Set account_type (main/farm/vacation)
2. Set linked_to_main (for farms only)
3. Fill in t4_deaths and t5_deaths
4. Add optional notes
"""
import pandas as pd
import requests

API_URL = "https://kd3584-production.up.railway.app"
SEASON_ID = "season_6"


def create_final_kvk_template():
    """Create Excel template with all players from current season."""
    print(f"📊 Fetching all players from {SEASON_ID}...")

    response = requests.get(
        f"{API_URL}/api/leaderboard",
        params={"kvk_season_id": SEASON_ID, "limit": 500}
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

    # Create template data
    template_data = []

    for player in players:
        gov_id = player['governor_id']
        gov_name = player['governor_name']
        total_deaths = player['stats']['deads']

        # Estimate 60/40 split for deaths as starting point
        estimated_t4 = int(total_deaths * 0.6)
        estimated_t5 = total_deaths - estimated_t4

        template_data.append({
            'governor_id': gov_id,
            'governor_name': gov_name,  # For reference only
            'account_type': 'main',  # Default to main, admin changes as needed
            'linked_to_main': '',  # Fill in for farms only
            't4_deaths': estimated_t4,  # Estimated - admin should verify
            't5_deaths': estimated_t5,  # Estimated - admin should verify
            'notes': ''
        })

    # Create DataFrame
    df = pd.DataFrame(template_data)
    filename = f'final_kvk_data_{SEASON_ID}.xlsx'

    # Save to Excel with formatting
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Final KvK Data')

        # Get worksheet
        worksheet = writer.sheets['Final KvK Data']

        # Set column widths
        worksheet.column_dimensions['A'].width = 15  # governor_id
        worksheet.column_dimensions['B'].width = 25  # governor_name
        worksheet.column_dimensions['C'].width = 15  # account_type
        worksheet.column_dimensions['D'].width = 15  # linked_to_main
        worksheet.column_dimensions['E'].width = 15  # t4_deaths
        worksheet.column_dimensions['F'].width = 15  # t5_deaths
        worksheet.column_dimensions['G'].width = 40  # notes

        # Add instructions comment to header
        from openpyxl.comments import Comment

        worksheet['C1'].comment = Comment(
            "Set to: main, farm, or vacation",
            "Admin"
        )

        worksheet['D1'].comment = Comment(
            "Only fill if account_type=farm\nEnter governor_id of main account",
            "Admin"
        )

        worksheet['E1'].comment = Comment(
            "Verify actual T4 deaths\n(Currently estimated)",
            "Admin"
        )

        worksheet['F1'].comment = Comment(
            "Verify actual T5 deaths\n(Currently estimated)",
            "Admin"
        )

    print(f"✅ Created final KvK template: {filename}")
    print()
    print("📋 Template includes:")
    print(f"   - {len(players)} players pre-filled")
    print(f"   - Estimated T4/T5 deaths (60/40 split)")
    print(f"   - All accounts default to 'main'")
    print()
    print("✏️ Admin tasks:")
    print("   1. Change account_type to 'farm' or 'vacation' as needed")
    print("   2. For farms: fill linked_to_main with main's governor_id")
    print("   3. Verify/correct T4 and T5 death counts")
    print("   4. Add optional notes")
    print()
    print("📤 Upload using: POST /admin/final-kvk/upload/{season_id}")
    print()

    return filename


def create_empty_template():
    """Create empty template for reference."""
    template_data = {
        'governor_id': ['12345678', '87654321', '11111111'],
        'governor_name': ['Example Player 1', 'Example Player 2 (Farm)', 'Example Player 3'],
        'account_type': ['main', 'farm', 'vacation'],
        'linked_to_main': ['', '12345678', ''],
        't4_deaths': [2800000, 500000, 0],
        't5_deaths': [1200000, 100000, 0],
        'notes': ['Top contributor', 'Farm of Player 1', 'Vacation ticket']
    }

    df = pd.DataFrame(template_data)
    filename = 'final_kvk_data_template_empty.xlsx'

    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Final KvK Data')

        worksheet = writer.sheets['Final KvK Data']
        worksheet.column_dimensions['A'].width = 15
        worksheet.column_dimensions['B'].width = 25
        worksheet.column_dimensions['C'].width = 15
        worksheet.column_dimensions['D'].width = 15
        worksheet.column_dimensions['E'].width = 15
        worksheet.column_dimensions['F'].width = 15
        worksheet.column_dimensions['G'].width = 40

    print(f"✅ Created empty reference template: {filename}")
    return filename


def main():
    print("=" * 70)
    print("📁 Creating Final KvK Data Templates")
    print("=" * 70)
    print()

    # Create empty reference template
    print("STEP 1: Creating empty reference template")
    print("-" * 70)
    empty_file = create_empty_template()
    print()

    # Create template with all players
    print("STEP 2: Creating template with all current players")
    print("-" * 70)
    full_file = create_final_kvk_template()
    print()

    print("=" * 70)
    print("✅ Templates Created Successfully!")
    print("=" * 70)
    print()
    print("Files created:")
    print(f"  1. {empty_file} - Empty reference template (examples)")
    print(f"  2. {full_file} - Full template with all {SEASON_ID} players")
    print()


if __name__ == "__main__":
    main()
