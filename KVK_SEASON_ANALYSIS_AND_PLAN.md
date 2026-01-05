# KVK Season System Analysis & Implementation Plan

## Part 1: KVK Season ID Analysis

### Current Implementation

**What is `kvk_season_id`?**

The `kvk_season_id` is a unique identifier that separates data from different Kingdom vs Kingdom events. Currently hardcoded as `"season_1"`.

### How It Works Across the System

**1. Database Collections (MongoDB)**

All three main collections use `kvk_season_id` as a partition key:

```javascript
// baselines collection
{
    "kvk_season_id": "season_1",  // ← Partition key
    "players": [...],
    "timestamp": "2026-01-10T..."
}

// current_data collection
{
    "kvk_season_id": "season_1",  // ← Partition key
    "players": [...],
    "timestamp": "2026-01-15T..."
}

// upload_history collection (multiple documents)
{
    "kvk_season_id": "season_1",  // ← Partition key
    "file_name": "day_5.xlsx",
    "players": [...],
    "timestamp": "2026-01-05T..."
}
```

**2. API Query Parameter**

All API endpoints accept `kvk_season_id` as a query parameter (defaults to `"season_1"`):

```python
# Example from backend/app/routes/players.py
@router.get("/leaderboard")
async def get_leaderboard(
    kvk_season_id: str = Query(default="season_1"),  # ← Defaults to season_1
    sort_by: str = Query(default="kill_points_gained"),
    limit: int = Query(default=100, le=500)
):
```

**3. Frontend Configuration**

Hardcoded in three JavaScript files:

```javascript
// frontend/public/script.js
const KVK_SEASON_ID = 'season_1';  // ← Hardcoded

// frontend/public/player.js
const KVK_SEASON_ID = 'season_1';  // ← Hardcoded

// frontend/public/admin.js
const seasonId = 'season_1';  // ← Default value in input fields
```

**4. Discord Bot Configuration**

Set via environment variable:

```python
# discord_bot/bot.py
KVK_SEASON_ID = os.getenv('KVK_SEASON_ID', 'season_1')  # ← From .env file
```

```bash
# discord_bot/.env
KVK_SEASON_ID=season_1
```

### Current Problems & Risks

❌ **Problem 1: No Season Isolation**

If you start a new KvK (season_2) without changing the season ID everywhere:
- New baseline will **overwrite** season_1 baseline
- New uploads will **mix** with season_1 data
- Historical data will be **corrupted**

❌ **Problem 2: Manual Updates Required**

To start a new season, you must manually update:
1. Frontend (3 files): `season_1` → `season_2`
2. Discord bot `.env`: `KVK_SEASON_ID=season_2`
3. Admin panel inputs: Change default values
4. Redeploy everything

❌ **Problem 3: No Archive Mechanism**

Current system has no way to:
- Mark a season as "complete" or "archived"
- Lock data from further edits
- List available seasons
- Switch between seasons

❌ **Problem 4: No Season Metadata**

No information stored about:
- Season start/end dates
- Season status (active, archived, deleted)
- Season description (KvK 1, KvK 2, Pre-KvK, etc.)
- Which kingdom participated

### Foolproofing Requirements

✅ **Must Have:**

1. **Active Season Management**
   - Admin selects "active" season
   - All uploads go to active season automatically
   - No manual season ID entry needed

2. **Season Archiving**
   - Mark season as "archived" when KvK ends
   - Archived seasons become read-only
   - No deletions or modifications allowed

3. **Season Metadata**
   - Start/end dates
   - Description
   - Status (preparing, active, archived)
   - Final results locked flag

4. **Season Switching**
   - Admin can switch between seasons to view historical data
   - Frontend shows current active season by default
   - Can browse archived seasons separately

5. **Data Isolation**
   - Each season's data completely separate
   - No accidental cross-contamination
   - Safe to have multiple seasons in database

---

## Part 2: Simplified Implementation Plan

Based on your requirements, here's the phased approach:

### Phase 1: Season Management Foundation ⭐ START HERE

**Goal**: Create robust season system with archiving

**What to Build:**

1. **Season Model**
   ```python
   class KvKSeason:
       season_id: str           # "season_1", "season_2", etc.
       season_name: str         # "KvK 1 - Season of Conquest"
       status: str              # "preparing", "active", "completed", "archived"
       start_date: datetime
       end_date: datetime
       is_active: bool          # Only ONE season can be active
       is_archived: bool        # Read-only when true
       final_data_uploaded: bool  # Final KvK data with verified deaths
       created_at: datetime
       archived_at: datetime
   ```

2. **Admin Panel - Season Management**
   - Create new season
   - Set season as active
   - Archive season (end of KvK)
   - View all seasons
   - Switch between seasons for viewing

3. **Database Changes**
   - New collection: `kvk_seasons`
   - Add `is_archived` checks before any data modification
   - Add `final_data_uploaded` flag

**Implementation Tasks:**

- [ ] Create `KvKSeason` model
- [ ] Create `/admin/seasons` API endpoints
- [ ] Add season management UI to admin panel
- [ ] Add "active season" selector to admin dashboard
- [ ] Implement archive protection (no edits when archived)
- [ ] Update all upload functions to use active season automatically

---

### Phase 2: Account Classification & Linking ⭐ YOUR PRIORITY #1

**Goal**: Admin can manually classify accounts and link farms to mains

**What to Build:**

1. **Player Account Types**
   ```python
   class AccountType(Enum):
       MAIN = "main"
       FARM = "farm"
       VACATION = "vacation"  # Vacation ticket holder
   ```

2. **Player Metadata (added to player documents)**
   ```python
   {
       "governor_id": "53242709",
       "governor_name": "ˢᵖBigWhale",
       "stats": {...},
       "delta": {...},

       # NEW FIELDS
       "account_type": "main",  # main, farm, vacation
       "linked_to_main": null,  # For farms: governor_id of main account
       "is_main_account": true,
       "farm_accounts": ["12345678", "98765432"]  # For mains: list of farm IDs
   }
   ```

3. **Admin Panel - Account Classification**
   ```
   Player Management
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Governor: ˢᵖBigWhale (53242709)
   Current Type: [Main ▼]

   [ ] This is a farm account
       Link to main: [Search Governor...]

   Farm Accounts (2):
   - FarmAcc1 (12345678) - 28M Power
   - FarmAcc2 (98765432) - 35M Power
   [+ Add Farm Account]

   [Save Classification]
   ```

4. **Leaderboard Logic Update**
   ```python
   def get_combined_player_data(main_player):
       """
       Combine main account stats with all linked farms
       """
       total_power = main_player.power
       total_kills = main_player.kill_points_gained
       # ... etc

       for farm_id in main_player.farm_accounts:
           farm = get_player(farm_id)
           total_power += farm.power
           total_kills += farm.kill_points_gained
           # ... etc

       return {
           "governor_id": main_player.governor_id,
           "governor_name": main_player.governor_name,
           "power": total_power,  # Combined power
           "kill_points_gained": total_kills,  # Combined kills
           "farms": [...]  # Details for dropdown
       }
   ```

**Implementation Tasks:**

- [ ] Add account_type fields to player model
- [ ] Create `/admin/classify-player` endpoint
- [ ] Create `/admin/link-farm-account` endpoint
- [ ] Build player classification UI
- [ ] Build farm linking UI
- [ ] Update leaderboard logic to combine main + farms
- [ ] Add expandable dropdown in leaderboard for farm details

---

### Phase 3: Verified Death Data Upload ⭐ YOUR PRIORITY #2

**Goal**: Upload Excel with verified T4/T5 deaths

**What to Build:**

1. **Excel Template Format**
   ```
   governor_id | t4_deaths | t5_deaths | notes
   53242709    | 2800000   | 1200000   | Good player
   51540567    | 1500000   | 800000    | Top warrior
   ```

2. **Upload Process**
   ```python
   async def upload_verified_deaths(excel_file, kvk_season_id):
       """
       1. Read Excel file
       2. For each row:
          - Find player in current_data
          - Update verified_deaths field
          - Mark as verified
       3. Recalculate contribution scores using new formula
       4. Update all ranks
       """
       for row in excel_data:
           player = find_player(row['governor_id'])

           player['verified_deaths'] = {
               't4_deaths': row['t4_deaths'],
               't5_deaths': row['t5_deaths'],
               'verified': True,
               'verified_at': datetime.now()
           }

           # Recalculate combat score with new weights
           player['combat_score'] = calculate_score_v2(player)
   ```

3. **New Contribution Formula (with verified deaths)**
   ```python
   def calculate_combat_score_v2(player):
       """
       Uses T4/T5 specific weights when verified data available
       """
       # Kills (from auto data - unchanged)
       t4_kill_score = player.t4_kills * 1
       t5_kill_score = player.t5_kills * 2

       # Deaths - NEW WEIGHTS
       if player.verified_deaths['verified']:
           t4_death_score = player.verified_deaths['t4_deaths'] * 4
           t5_death_score = player.verified_deaths['t5_deaths'] * 8  # 2x T4
       else:
           # Fallback: Use total deaths with average weight
           avg_weight = 5  # Midpoint between 4 and 8
           death_score = player.total_deaths * avg_weight

       return kill_score + death_score
   ```

4. **Admin Panel - Death Upload**
   ```
   Upload Verified Death Data
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Excel File: [Choose File: verified_deaths.xlsx]
   [Upload & Verify]

   Preview (5 rows):
   ┌─────────────────────────────────────────────┐
   │ ˢᵖBigWhale: T4=2.8M, T5=1.2M ✅ Match       │
   │ ⚔️Warrior: T4=1.5M, T5=800k ✅ Match        │
   │ F2PHero: T4=500k, T5=150k ⚠️ NEW DATA      │
   └─────────────────────────────────────────────┘

   Status: 180/205 players verified (87.8%)

   [Process Upload] [Cancel]
   ```

**Implementation Tasks:**

- [ ] Add `verified_deaths` field to player model
- [ ] Create Excel template for deaths
- [ ] Create `/admin/upload-verified-deaths` endpoint
- [ ] Build death upload UI with preview
- [ ] Update `calculate_combat_score()` to use verified deaths
- [ ] Add verification status indicator in admin panel

---

### Phase 4: Final KvK Data & Archiving ⭐ END OF KVK

**Goal**: Upload comprehensive final data and archive season

**What to Build:**

1. **Final KvK Excel Format**
   ```
   governor_id | account_type | linked_to_main | t4_deaths | t5_deaths | notes
   53242709    | main         | null           | 2800000   | 1200000   | Top player
   12345678    | farm         | 53242709       | 500000    | 100000    | Farm of BigWhale
   98765432    | vacation     | null           | 0         | 0         | Vacation ticket
   ```

2. **Final Upload Process**
   ```python
   async def upload_final_kvk_data(excel_file, kvk_season_id):
       """
       COMPREHENSIVE END-OF-KVK DATA UPLOAD

       1. Classify all accounts (main/farm/vacation)
       2. Link farms to mains
       3. Update verified deaths
       4. Recalculate all contribution scores
       5. Generate final rankings (with farm combinations)
       6. Mark season as completed
       """

       for row in excel_data:
           player = find_player(row['governor_id'])

           # Classify account
           player['account_type'] = row['account_type']

           # Link farms
           if row['account_type'] == 'farm':
               player['linked_to_main'] = row['linked_to_main']
               main = find_player(row['linked_to_main'])
               main['farm_accounts'].append(row['governor_id'])

           # Verified deaths
           player['verified_deaths'] = {
               't4_deaths': row['t4_deaths'],
               't5_deaths': row['t5_deaths'],
               'verified': True
           }

       # Recalculate everything
       recalculate_all_scores()
       generate_final_rankings()

       # Mark season complete
       season = get_season(kvk_season_id)
       season['status'] = 'completed'
       season['final_data_uploaded'] = True
   ```

3. **Final Leaderboard Display**
   ```
   🏆 Final KvK Rankings - Season 1

   Rank | Player           | Power    | Contribution | Details
   ─────┼──────────────────┼──────────┼──────────────┼─────────
   1    | ˢᵖBigWhale [▼]  | 365M     | 8.45%        | ▼ View Farms
        │ ├─ Main          │ 200M     │ 5.31%        │
        │ ├─ Farm1         │ 85M      │ 1.82%        │
        │ └─ Farm2         │ 80M      │ 1.32%        │
   2    | ⚔️Warrior        | 80M      | 4.49%        |
   3    | F2PHero          | 35M      | 1.73%        |
   ```

4. **Archive Season Function**
   ```python
   async def archive_season(kvk_season_id):
       """
       1. Verify final data uploaded
       2. Set status = "archived"
       3. Set is_archived = True (read-only)
       4. Lock all data (no more uploads)
       5. Generate final report
       """
       season = get_season(kvk_season_id)

       if not season['final_data_uploaded']:
           raise Error("Cannot archive: Final data not uploaded")

       season['status'] = 'archived'
       season['is_archived'] = True
       season['archived_at'] = datetime.now()

       # Create historical snapshot
       create_archive_snapshot(season)
   ```

**Implementation Tasks:**

- [ ] Create comprehensive Excel template
- [ ] Create `/admin/upload-final-kvk-data` endpoint
- [ ] Build final upload UI with validation
- [ ] Implement farm combination logic for final rankings
- [ ] Create `/admin/archive-season` endpoint
- [ ] Build archive confirmation UI
- [ ] Update leaderboard to show combined main+farm data
- [ ] Add expandable farm details in leaderboard

---

### Phase 5: New Season Preparation

**Goal**: Start fresh for next KvK

**What to Build:**

1. **Create New Season**
   ```
   Create New KvK Season
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Season ID: [season_2    ]
   Season Name: [KvK 2 - Season of Valor]
   Start Date: [2026-02-01  ]
   Description: [KvK 2 against Kingdom 3585]

   [Create Season]
   ```

2. **Auto-Activation**
   ```python
   async def create_new_season(season_data):
       """
       1. Create season record
       2. Set as active (deactivate previous)
       3. Clear admin panel for new uploads
       4. Reset frontend to new season
       """
       # Deactivate all other seasons
       await seasons_collection.update_many(
           {},
           {"$set": {"is_active": False}}
       )

       # Create new season
       new_season = {
           "season_id": season_data['season_id'],
           "is_active": True,
           "status": "preparing",
           "final_data_uploaded": False
       }

       await seasons_collection.insert_one(new_season)

       # Auto-update frontend config
       update_active_season(season_data['season_id'])
   ```

**Implementation Tasks:**

- [ ] Create "New Season" form in admin panel
- [ ] Auto-deactivate old season when creating new
- [ ] Clear admin panel state
- [ ] Update API to use active season automatically
- [ ] Add season switcher in frontend for viewing archives

---

## Part 3: Zeroing Penalty Calculation

### Problem: Determining Fair Penalty for Zeroed Players

When a player gets zeroed, we need to determine what % of their deaths to count.

### Research-Based Recommendations

From community research:
> "If you are zeroed with terrible trade, your death of that day will be counted as 0"

**Trade Ratio Formula:**
```
Trade Ratio = Kill Points Gained / Death Power

Where Death Power = (T4 deaths × 16) + (T5 deaths × 20)
```

**Community Standards:**

| Trade Ratio | Quality | Recommendation |
|------------|---------|----------------|
| ≥ 1.5 | Excellent | 100% credit (won the trade) |
| 1.0 - 1.5 | Good | 100% credit (even or slight win) |
| 0.5 - 1.0 | Fair | 70-80% credit (acceptable losses) |
| 0.3 - 0.5 | Poor | 30-50% credit (heavy losses but fought) |
| < 0.3 | Terrible | 0-20% credit (zeroed without fighting) |

### Recommended Penalty Table

For players who got zeroed, manually calculate their trade ratio and apply:

**Option A: Conservative (Strict)**
```
Trade Ratio < 0.3 → 0% credit (zero out all deaths)
Trade Ratio 0.3-0.5 → 30% credit
Trade Ratio 0.5-1.0 → 70% credit
Trade Ratio ≥ 1.0 → 100% credit
```

**Option B: Moderate (Balanced)** ⭐ RECOMMENDED
```
Trade Ratio < 0.2 → 0% credit (complete zero/no fight)
Trade Ratio 0.2-0.4 → 25% credit
Trade Ratio 0.4-0.7 → 50% credit
Trade Ratio 0.7-1.0 → 75% credit
Trade Ratio ≥ 1.0 → 100% credit
```

**Option C: Lenient (Forgiving)**
```
Trade Ratio < 0.15 → 0% credit
Trade Ratio 0.15-0.3 → 40% credit
Trade Ratio 0.3-0.6 → 60% credit
Trade Ratio 0.6-1.0 → 80% credit
Trade Ratio ≥ 1.0 → 100% credit
```

### Example Calculation

**Player: Gets Zeroed**
```
T4 Deaths: 3,000,000
T5 Deaths: 1,500,000
Total Death Power = (3M × 16) + (1.5M × 20) = 48M + 30M = 78M

Kill Points Gained: 15,000,000

Trade Ratio = 15M / 78M = 0.19 (Terrible trade)
```

**Applying Option B (Recommended):**
- Trade Ratio 0.19 is between 0.2-0.4
- **Apply 25% credit**

**Final Deaths for Contribution:**
```
Adjusted T4 Deaths = 3,000,000 × 0.25 = 750,000
Adjusted T5 Deaths = 1,500,000 × 0.25 = 375,000

Combat Score = (T4 kills × 1) + (T5 kills × 2) + (750k × 4) + (375k × 8)
             = ... + 3M + 3M
             = ... + 6M (instead of 24M without penalty)
```

### Manual Workflow for Zeroed Players

1. **Identify zeroed players** (sudden death spike > 4M troops)
2. **Calculate trade ratio** from their battle reports
3. **Apply penalty %** from table above
4. **Adjust T4/T5 death counts** in final Excel upload
5. **Add note** in Excel for transparency

**Example Excel Entry:**
```
governor_id | t4_deaths | t5_deaths | notes
11111111    | 750000    | 375000    | Zeroed: Trade ratio 0.19, applied 25% penalty
```

This way, you manually calculate and enter the adjusted numbers, and the system just uses them directly.

---

## Summary: Implementation Order

### Month 1: Foundation
1. ✅ Phase 1: Season Management (Week 1-2)
2. ✅ Phase 2: Account Classification (Week 3-4)

### Month 2: Death Tracking
3. ✅ Phase 3: Verified Death Upload (Week 1-2)
4. ✅ Phase 4: Final KvK Data & Archive (Week 3-4)

### Month 3: Polish
5. ✅ Phase 5: New Season Preparation (Week 1)
6. ✅ Testing & Refinement (Week 2-4)

---

## Next Steps

**Question for You:**

1. **Trade Ratio Penalty**: Which option do you prefer?
   - A: Conservative (strict penalties)
   - B: Moderate (balanced) ⭐ Recommended
   - C: Lenient (forgiving)

2. **Implementation Start**: Should we start with Phase 1 (Season Management) or Phase 2 (Account Classification)?

3. **Excel Templates**: Should I create downloadable Excel templates now for:
   - Verified deaths upload
   - Final KvK data upload

4. **Season Naming**: How do you want to name seasons?
   - Simple: "season_1", "season_2", "season_3"
   - Descriptive: "kvk1_jan2026", "kvk2_mar2026"
   - Custom: You provide names

Let me know your preferences and we'll start building!
