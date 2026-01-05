# Advanced Contribution System - Solutions for Real-World Problems

## Problem Statement Summary

Based on your requirements, we need to solve:

1. **Zeroing Problem**: Players getting rallied and zeroed unfairly inflate death counts
2. **Troop Tier Tracking**: Current data only shows total deaths, not T4/T5 breakdown
3. **Manual Data Entry**: Need admin panel to input accurate T4/T5 death counts from screenshots
4. **Final KvK Data**: Option to upload comprehensive Excel file with verified data
5. **Farm Accounts**: Need to identify and exclude farm accounts from rankings
6. **Dead Weight**: Identify and handle inactive/non-contributing players

---

## Research Findings: Key Insights

### What is "Zeroing"?

**Definition**: When a player gets "zeroed," it means **all their troops have been killed** through sustained enemy attacks. The city **teleports randomly** when completely zeroed.

**Typical Death Counts When Zeroed:**
- Regular players: **10-35 million troops**
- High-power whales: **4-5 million T5 troops** + lower tiers
- One documented case: ~35 million premium troops (~$250k value)

**Kingdom DKP Rules for Zeroing:**
> "If you are zeroed with terrible trade, your death of that day will be counted as 0"

This means **only deaths with proportional kills count** toward contribution.

### T4 vs T5 Death Values

**Resource Cost Comparison:**
- **T4**: 72M Food, 72M Wood, 54M Stone, 7.2M Gold
- **T5**: 192M Food, 192M Wood, 144M Stone, 144M Gold
- **Multipliers**: Food/Wood/Stone = **2.67x**, Gold = **20x**

**Community Standard Formulas:**

**Kingdom 2296 (Most Balanced):**
```
DKP = (T4 kills × 1) + (T5 kills × 2) + (T4 deaths × 3) + (T5 deaths × 5)
```
- T5 death weight = **1.67x** T4 death weight

**Kingdom Alternative:**
```
DKP = (T4 kills × 1) + (T5 kills × 5.25) + (T4 deaths × 5) + (T5 deaths × 10)
```
- T5 death weight = **2x** T4 death weight

**Recommended Standard:**
```
T5 deaths should be worth 2x T4 deaths (reflects resource cost)
```

### Farm Account Identification Criteria

**Automated Detection:**
1. **Power threshold**: < 30-40M power
2. **City Hall level**: < CH22
3. **Naming pattern**: Contains "farm", "alt", "2", or matches main account name
4. **Development pattern**: Minimal military research, maxed gathering

**Manual Registration:**
- Players declare their farm accounts
- Combine DKP from alts into main account OR
- Exclude farms from competitive rankings

### Dead Weight Identification

**Activity Indicators:**
- Minimal kills (< 25M troops killed)
- Minimal deaths (< 10M troops lost)
- High power but low DKP (top 300 power, bottom 50% DKP)
- Zero honor points from building occupation

**Kingdom Penalties:**
- **Negative DKP** = Forced migration or zeroing
- **Top 300 power + low DKP** = Exile after KvK
- **Two choices**: Migrate within 7 days OR delete troops

---

## Proposed Solution: Enhanced Contribution System

### Solution 1: **Bad Trade Detection & Flagging** ⭐ CRITICAL

When a player gets zeroed, we need to determine if it was a "good trade" or "bad trade."

#### Algorithm:

```python
def calculate_trade_ratio(player_snapshot):
    """
    Determine if deaths were from good combat or bad zeroing

    Returns:
        - trade_ratio: Kill points / Death power
        - trade_quality: "excellent", "good", "fair", "poor", "terrible"
    """
    kill_points = player_snapshot.kill_points_gained
    death_power = calculate_death_power(player_snapshot.deads_gained)

    if death_power == 0:
        return 0, "no_combat"

    trade_ratio = kill_points / death_power

    # Classify trade quality
    if trade_ratio >= 1.5:
        return trade_ratio, "excellent"  # 50%+ positive trade
    elif trade_ratio >= 1.0:
        return trade_ratio, "good"       # Even or positive trade
    elif trade_ratio >= 0.5:
        return trade_ratio, "fair"       # Acceptable losses
    elif trade_ratio >= 0.3:
        return trade_ratio, "poor"       # Heavy losses but fought
    else:
        return trade_ratio, "terrible"   # Zeroed without fight

def calculate_death_power(total_deaths):
    """
    Estimate death power from total death count
    Assumes average troop tier distribution
    """
    # Conservative estimate: 60% T4, 30% T5, 10% T3
    estimated_power = (
        total_deaths * 0.60 * 16 +  # T4 = 16 power each
        total_deaths * 0.30 * 20 +  # T5 = 20 power each
        total_deaths * 0.10 * 8     # T3 = 8 power each
    )
    return estimated_power
```

#### Admin Panel Flagging:

**UI Mockup:**
```
Upload History - Flagging Interface
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Upload: Day 15 - Major Rally Event
Date: Jan 10, 2026

Players with Suspicious Death Spikes:
┌────────────────────────────────────────────────────────────┐
│ Governor: ˢᵖBigWhale (ID: 53242709)                        │
│ Deaths Gained: 4,500,000 (+4.2M from previous)            │
│ Kills Gained: 500,000                                       │
│ Trade Ratio: 0.12 (TERRIBLE) ⚠️                            │
│                                                             │
│ [ ] Normal Combat (Count full deaths)                      │
│ [x] Bad Trade/Zeroed (Apply penalty)                       │
│     Penalty: [ 100% exclusion ] [ 50% weight ] [ Custom ]  │
│                                                             │
│ Notes: _______________________________________________     │
│                                                             │
│ [Save Flag]  [Clear Flag]                                  │
└────────────────────────────────────────────────────────────┘
```

#### Penalty Options:

**Option A: Complete Exclusion (Recommended)**
```python
if player.flagged_as_bad_trade:
    death_contribution = 0  # Zero out deaths for this upload period
    # Contribution from previous uploads remains unchanged
```

**Option B: Partial Credit (50%)**
```python
if player.flagged_as_bad_trade:
    death_contribution = player.deaths_gained * 0.5  # Half credit
```

**Option C: Progressive Penalty (Based on Trade Ratio)**
```python
def calculate_death_penalty(trade_ratio):
    """
    Excellent (>1.5): 100% credit
    Good (1.0-1.5): 100% credit
    Fair (0.5-1.0): 80% credit
    Poor (0.3-0.5): 50% credit
    Terrible (<0.3): 0% credit (flagged as bad trade)
    """
    if trade_ratio >= 1.0:
        return 1.0
    elif trade_ratio >= 0.5:
        return 0.8
    elif trade_ratio >= 0.3:
        return 0.5
    else:
        return 0.0  # Bad trade
```

**Recommended: Option A (Complete Exclusion)**
- Clear and fair
- Prevents exploitation
- Matches community standards
- Player contribution "freezes" at moment before zeroing

---

### Solution 2: **T4/T5 Death Tracking** ⭐ CRITICAL

Since game data doesn't provide T4/T5 breakdown, we need manual entry system.

#### Data Structure Enhancement:

```python
class PlayerSnapshot:
    # Existing fields
    governor_id: str
    stats: dict
    delta: dict

    # NEW: Detailed death breakdown
    verified_deaths: dict = {
        "t4_deaths": 0,
        "t5_deaths": 0,
        "verified": False,  # Admin has verified screenshot
        "screenshot_url": None,
        "verified_by": None,  # Admin username
        "verified_at": None   # Timestamp
    }
```

#### Admin Panel - Manual Death Entry:

**UI Mockup:**
```
Manual Death Data Entry - Upload: Day 15
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Search Player: [ˢᵖBigWhale          ] [Search]

┌────────────────────────────────────────────────────────────┐
│ Governor: ˢᵖBigWhale (ID: 53242709)                        │
│ Total Deaths (Auto): 4,500,000                              │
│                                                             │
│ Manual Verification:                                        │
│   T4 Deaths: [2,800,000      ] troops                      │
│   T5 Deaths: [1,200,000      ] troops                      │
│   Total:     3,200,000 (71% of auto-detected)              │
│                                                             │
│ Screenshot Upload:                                          │
│   [Upload Screenshot] [📎 deaths_screenshot.jpg] [View]    │
│                                                             │
│ Status: ⚠️ Unverified                                       │
│                                                             │
│ [ ] Mark as Verified                                        │
│                                                             │
│ [Save Data]  [Clear]                                        │
└────────────────────────────────────────────────────────────┘

Bulk Import from Excel: [Choose File] [Import]
Expected format: governor_id, t4_deaths, t5_deaths
```

#### Contribution Calculation with Verified Deaths:

```python
def calculate_combat_score_v2(player):
    """
    Enhanced DKP with T4/T5 death breakdown
    """
    t4_kill_weight = 1
    t5_kill_weight = 3
    t4_death_weight = 4
    t5_death_weight = 8  # 2x T4 death weight

    # Kills (from auto data)
    kill_score = (
        player.t4_kills * t4_kill_weight +
        player.t5_kills * t5_kill_weight
    )

    # Deaths - use verified data if available
    if player.verified_deaths['verified']:
        death_score = (
            player.verified_deaths['t4_deaths'] * t4_death_weight +
            player.verified_deaths['t5_deaths'] * t5_death_weight
        )
    else:
        # Fallback: Use total deaths with average weight
        # Assume 60% T4, 40% T5 distribution
        avg_death_weight = (0.6 * t4_death_weight) + (0.4 * t5_death_weight)
        death_score = player.total_deaths * avg_death_weight

    # Apply bad trade penalty if flagged
    if player.flagged_as_bad_trade:
        death_score = 0

    return kill_score + death_score
```

#### Excel Import Format:

**Template: `final_kvk_deaths.xlsx`**

| governor_id | governor_name | t4_deaths | t5_deaths | screenshot_ref | notes |
|------------|---------------|-----------|-----------|----------------|-------|
| 53242709 | ˢᵖBigWhale | 2800000 | 1200000 | whale_deaths.jpg | Verified from screenshot |
| 51540567 | ⚔️Warrior | 1500000 | 800000 | warrior_deaths.jpg | Good trade |
| 46489463 | F2PHero | 500000 | 150000 | f2p_deaths.jpg | Minimal losses |

**Import Process:**
1. Admin uploads Excel file
2. System validates governor IDs exist
3. Maps data to player records
4. Marks all as "verified"
5. Recalculates all contribution scores
6. Shows diff report of changes

---

### Solution 3: **Final KvK Data Upload** ⭐ NEW FEATURE

After KvK ends, admin uploads comprehensive Excel with all corrections.

#### File Format:

**Template: `final_kvk_comprehensive.xlsx`**

| governor_id | account_type | exclude_ranking | t4_deaths | t5_deaths | bad_trade_flag | notes |
|------------|--------------|-----------------|-----------|-----------|----------------|-------|
| 53242709 | main | false | 2800000 | 1200000 | false | Good player |
| 51540567 | main | false | 1500000 | 800000 | false | Top warrior |
| 46489463 | main | false | 500000 | 150000 | false | F2P hero |
| 12345678 | farm | true | 0 | 0 | false | Alt account |
| 98765432 | dead_weight | true | 50000 | 0 | false | Inactive |
| 11111111 | main | false | 5000000 | 2000000 | true | Zeroed badly |

**Columns Explained:**
- `account_type`: main, farm, dead_weight, migrated
- `exclude_ranking`: true/false - remove from leaderboards
- `t4_deaths` / `t5_deaths`: Verified from screenshots
- `bad_trade_flag`: true = zero out deaths for contribution
- `notes`: Admin notes for reference

#### Admin Panel - Final Upload:

**UI Mockup:**
```
Final KvK Data Upload
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ WARNING: This will override all automatic calculations
with verified data. Use this at the END of KvK season.

Upload Final Data File:
[Choose File: final_kvk_comprehensive.xlsx] [Upload]

Preview Changes:
┌────────────────────────────────────────────────────────────┐
│ 205 players total                                           │
│ - 165 Main accounts (will be ranked)                       │
│ - 25 Farm accounts (excluded from ranking)                 │
│ - 10 Dead weight (excluded)                                │
│ - 5 Bad trade flags (deaths zeroed)                        │
│                                                             │
│ T4/T5 Death Data:                                           │
│ - 180 players with verified T4/T5 breakdown                │
│ - 25 players using estimated breakdown                     │
│                                                             │
│ Contribution Score Changes:                                 │
│ - 42 players will see score increase                       │
│ - 31 players will see score decrease                       │
│ - 132 players unchanged                                     │
│                                                             │
│ [ ] I have reviewed all data and confirm upload            │
│                                                             │
│ [Process Upload]  [Cancel]                                 │
└────────────────────────────────────────────────────────────┘
```

---

### Solution 4: **Player Classification System** ⭐ ADMIN TOOLS

#### Player Types:

```python
class PlayerType(Enum):
    MAIN = "main"              # Primary account, included in rankings
    FARM = "farm"              # Alt account for resources, excluded
    DEAD_WEIGHT = "dead_weight"  # Inactive, excluded
    MIGRATED = "migrated"      # Left kingdom, excluded
    BANNED = "banned"          # Rule violator, excluded
```

#### Auto-Detection Algorithm:

```python
def classify_player_type(player):
    """
    Automatically classify player type based on criteria
    Admin can override
    """
    # Farm account detection
    if (player.power < 40_000_000 and
        player.city_hall_level < 22 and
        player.kill_points_gained < 1_000_000):
        return PlayerType.FARM

    # Dead weight detection
    if (player.power > 50_000_000 and
        player.kill_points_gained < 5_000_000 and
        player.deads_gained < 1_000_000):
        return PlayerType.DEAD_WEIGHT

    # Default: main account
    return PlayerType.MAIN

def should_include_in_ranking(player):
    """
    Determine if player should appear in leaderboards
    """
    if player.account_type in [PlayerType.FARM, PlayerType.DEAD_WEIGHT,
                                PlayerType.MIGRATED, PlayerType.BANNED]:
        return False

    if player.exclude_from_ranking:  # Manual flag
        return False

    return True
```

#### Admin Panel - Player Management:

**UI Mockup:**
```
Player Classification & Management
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Filter: [All ▼] [Main] [Farm] [Dead Weight] [Migrated]
Search: [____________] [Search]

┌────────────────────────────────────────────────────────────┐
│ ˢᵖBigWhale (53242709) - 200M Power                         │
│ Type: [Main ▼] Status: ✅ Included in Rankings             │
│ Auto-Detected: Main (High power + active)                  │
│ KP Gained: 26.5M | Deaths: 3.2M | Contribution: 5.31%     │
│ [Save] [Flag as Dead Weight]                               │
├────────────────────────────────────────────────────────────┤
│ FarmAcc2 (12345678) - 28M Power                            │
│ Type: [Farm ▼] Status: ❌ Excluded from Rankings           │
│ Auto-Detected: Farm (Low power + minimal activity)         │
│ KP Gained: 850k | Deaths: 150k | Contribution: N/A        │
│ [Save] [Change to Main]                                    │
├────────────────────────────────────────────────────────────┤
│ Inactive123 (98765432) - 65M Power                         │
│ Type: [Dead Weight ▼] Status: ⚠️ Excluded                  │
│ Auto-Detected: Dead Weight (High power + no activity)      │
│ KP Gained: 1.2M | Deaths: 250k | Contribution: N/A        │
│ [Save] [Send Warning Message]                              │
└────────────────────────────────────────────────────────────┘

Bulk Actions:
[Import Classifications from Excel] [Export Current Classifications]

Statistics:
- Main Accounts: 165 (included in rankings)
- Farm Accounts: 25 (excluded)
- Dead Weight: 10 (excluded)
- Migrated: 5 (excluded)
```

---

### Solution 5: **Enhanced Admin Panel Features**

#### New Admin Panel Sections:

**1. Data Verification Dashboard**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Data Quality Dashboard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Upload: Day 15 - Major Rally Event

Verification Status:
✅ T4/T5 Deaths Verified: 180/205 players (87.8%)
⚠️ Pending Verification: 25 players
❌ Flagged Bad Trades: 5 players

Auto-Detected Issues:
🚨 Suspicious Death Spikes: 8 players (review needed)
⚠️ Possible Farms: 12 players (confirm classification)
⚠️ Dead Weight Candidates: 6 players (send warnings)

[Review Suspicious Activity] [Verify Pending Deaths]
```

**2. Batch Operations**
```
Batch Player Operations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ ] Select All Dead Weight (10 players)
[ ] Select All Unverified Deaths (25 players)
[ ] Select All Bad Trade Flags (5 players)

Actions:
[Send Warning Email] [Exclude from Rankings]
[Request Screenshot Verification] [Export to Excel]
```

**3. Historical Comparison**
```
Compare Uploads
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Upload 1: [Day 10 ▼]  vs  Upload 2: [Day 15 ▼]

Top Changes:
┌────────────────────────────────────────────────────────────┐
│ ˢᵖBigWhale: +4.2M deaths ⚠️ (Investigate)                  │
│ ⚔️Warrior: +2.1M kills ✅ (Good performance)                │
│ Inactive123: +50k kills ⚠️ (Minimal activity)              │
└────────────────────────────────────────────────────────────┘

[Generate Report] [Flag Anomalies]
```

---

## Recommended Workflow

### During KvK (Weekly):

1. **Upload Current Data** (CSV/Excel)
   - System auto-calculates everything
   - Flags suspicious death spikes
   - Auto-classifies farm/dead weight

2. **Review Flagged Players**
   - Check trade ratios
   - Flag bad trades (deaths zeroed)
   - Verify farm account classifications

3. **Manual Death Verification** (Optional)
   - Players submit screenshots
   - Admin enters T4/T5 breakdown
   - System recalculates contribution

4. **Publish Rankings**
   - Only "main" accounts shown
   - Farms and dead weight excluded
   - Bad trades have deaths zeroed

### After KvK (Final):

1. **Collect All Screenshots**
   - Request T4/T5 death data from all players
   - Verify top 50 contributors

2. **Create Final Excel File**
   ```
   governor_id | account_type | t4_deaths | t5_deaths | bad_trade_flag
   ```

3. **Upload Final KvK Data**
   - System processes comprehensive file
   - Recalculates all scores with verified data
   - Generates final rankings

4. **Lock Season Data**
   - Mark season as "complete"
   - No further edits allowed
   - Archive for historical comparison

---

## Implementation Summary

### Database Schema Changes:

```python
# Player document in upload_history
{
    "governor_id": "53242709",
    "governor_name": "ˢᵖBigWhale",
    "rank": 12,
    "stats": {...},
    "delta": {...},

    # NEW FIELDS
    "account_type": "main",  # main, farm, dead_weight, migrated, banned
    "exclude_from_ranking": false,

    "verified_deaths": {
        "t4_deaths": 2800000,
        "t5_deaths": 1200000,
        "verified": true,
        "verified_by": "admin_user",
        "verified_at": "2026-01-15T10:30:00Z",
        "screenshot_url": "uploads/deaths/53242709_day15.jpg"
    },

    "trade_analysis": {
        "trade_ratio": 0.42,
        "trade_quality": "fair",
        "flagged_as_bad_trade": false,
        "flagged_by": null,
        "flag_reason": null
    },

    "contribution_breakdown": {
        "kill_score": 14500000,
        "death_score": 11500000,
        "total_score": 26000000,
        "contribution_pct": 5.31
    }
}
```

### New API Endpoints:

```
POST /api/admin/flag-bad-trade
POST /api/admin/verify-deaths
POST /api/admin/classify-player
POST /api/admin/upload-final-kvk-data
POST /api/admin/batch-operations

GET /api/admin/verification-status
GET /api/admin/flagged-players
GET /api/admin/unverified-deaths
```

### Admin Panel Routes:

```
/admin/data-verification      - Dashboard for data quality
/admin/manual-death-entry     - Enter T4/T5 deaths
/admin/player-classification  - Manage account types
/admin/bad-trade-flagging     - Flag zeroed players
/admin/final-upload           - End of KvK comprehensive upload
/admin/batch-operations       - Bulk actions
```

---

## Next Steps - What Do You Think?

Please review and provide feedback on:

1. **Bad Trade Handling**: Is complete exclusion (0% credit) fair? Or prefer partial credit (50%)?

2. **T4/T5 Death Weights**: Is 2x multiplier (T5 = 8 points, T4 = 4 points) appropriate?

3. **Farm Detection**: Should auto-detection be strict (<40M power) or lenient (<30M)?

4. **Dead Weight Threshold**: What's minimum acceptable contribution? (Suggest: 25M kills OR 10M deaths)

5. **Final Upload Workflow**: Do you want weekly manual verification OR only final comprehensive upload?

6. **Excel Templates**: Should I create downloadable Excel templates with formulas?

Let me know your preferences and we can proceed with implementation!
