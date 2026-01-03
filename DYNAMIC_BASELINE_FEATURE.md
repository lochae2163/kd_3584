# Dynamic Baseline Management Feature

## Overview

The system now **automatically adds new governors to the baseline** when they first appear in uploaded data, with their deltas starting at zero. This prevents misleading statistics where a new player's full stats would show as "gained."

## How It Works

### Before This Feature ❌

When a new governor appeared in current data:
```
Baseline: [Player A, Player B, Player C]
Current:  [Player A, Player B, Player C, Player D (NEW)]

Player D Result:
- Stats: 100M power, 500M KP
- Delta: +100M power, +500M KP  ❌ MISLEADING!
  (Shows full stats as "gained" since no baseline existed)
```

### After This Feature ✅

When a new governor appears in current data:
```
Baseline: [Player A, Player B, Player C]
Current:  [Player A, Player B, Player C, Player D (NEW)]

Player D Result:
- Stats: 100M power, 500M KP
- Delta: +0 power, +0 KP  ✅ CORRECT!
  (Their current stats become their new baseline)

Updated Baseline: [Player A, Player B, Player C, Player D]
  (Player D is now permanently in the baseline for future comparisons)
```

## Implementation Details

### 1. Detection Logic (`data_model.py`)

```python
def calculate_all_deltas(baseline_players, current_players):
    for player in current_players:
        if player_in_baseline:
            # Existing player - calculate delta normally
            delta = current_stats - baseline_stats
        else:
            # NEW PLAYER - use current stats as new baseline
            baseline_stats = current_stats  # Set current as baseline
            delta = 0 for all stats        # Zero deltas
            mark as newly_added_to_baseline = True
```

### 2. Persistence Logic (`ml_service.py`)

```python
async def process_and_save_current():
    # Calculate deltas (includes new player detection)
    players_with_deltas = calculate_all_deltas(baseline, current)

    # Find new players
    new_players = [p for p in players_with_deltas
                   if p.get('newly_added_to_baseline')]

    if new_players:
        # Add to baseline in database
        baseline_players.append(new_players)
        await database.update_baseline(baseline_players)

        logger.info(f"Added {len(new_players)} new players to baseline")
```

### 3. Database Updates

The baseline document is automatically updated:
```json
{
  "kvk_season_id": "season_1",
  "players": [...existing players..., ...new players...],
  "player_count": 204 → 210,
  "last_updated": "2026-01-03T10:30:00Z"
}
```

## Use Cases

### Use Case 1: New Alliance Member Joins
```
Day 1: Upload baseline (200 players)
Day 5: New member joins alliance
Day 6: Upload current data (201 players)

Result:
- New member shows in leaderboard
- Their deltas are all zero
- Future uploads will track their progress from Day 6
```

### Use Case 2: Player Resets/Migrates
```
Baseline: Player "John" ID 12345 (100M power)
Current:  Player "John" ID 99999 (50M power) - NEW ID

Result:
- ID 99999 is treated as a new player
- Zero deltas for ID 99999
- ID 12345 no longer appears in current data
```

### Use Case 3: Multiple New Players
```
Upload 1: Baseline with 200 players
Upload 2: +5 new players → Baseline updated to 205
Upload 3: +3 new players → Baseline updated to 208
Upload 4: +2 new players → Baseline updated to 210

Each group gets zero deltas on first appearance
Future uploads track their progress correctly
```

## Benefits

### ✅ Accurate Delta Reporting
- New players don't pollute top gainers lists
- Deltas represent actual growth, not initial stats
- Fair comparison between all players

### ✅ No Manual Intervention
- Admins don't need to re-upload baseline
- System handles new players automatically
- Baseline grows dynamically

### ✅ Honest Statistics
- Discord bot shows realistic "gained" numbers
- Web leaderboard reflects true performance
- Rankings are based on actual progress

### ✅ Maintains History
- All uploads are logged to history collection
- Can track when each player was added
- Baseline evolution is preserved

## Technical Implementation

### Files Modified

1. **`backend/app/ml/data_model.py`**
   - `calculate_all_deltas()` method
   - Lines: 437-505

2. **`backend/app/services/ml_service.py`**
   - `process_and_save_current()` method (CSV)
   - `process_and_save_current_excel()` method (Excel)
   - Lines: 111-215, 217-305

### Database Schema

**Baseline Document:**
```json
{
  "_id": ObjectId("..."),
  "type": "baseline",
  "kvk_season_id": "season_1",
  "players": [
    {
      "governor_id": "12345",
      "governor_name": "PlayerName",
      "stats": {
        "power": 100000000,
        "kill_points": 500000000,
        "deads": 10000000,
        "t4_kills": 50000000,
        "t5_kills": 30000000
      }
    }
  ],
  "player_count": 204,
  "last_updated": "2026-01-03T10:30:00Z"
}
```

**Player with Delta (API Response):**
```json
{
  "governor_id": "12345",
  "governor_name": "PlayerName",
  "stats": {
    "power": 105000000,
    "kill_points": 550000000,
    "deads": 11000000,
    "t4_kills": 52000000,
    "t5_kills": 32000000
  },
  "delta": {
    "power": 5000000,
    "kill_points": 50000000,
    "deads": 1000000,
    "t4_kills": 2000000,
    "t5_kills": 2000000
  },
  "in_baseline": true,
  "newly_added_to_baseline": false
}
```

**New Player (API Response):**
```json
{
  "governor_id": "99999",
  "governor_name": "NewPlayer",
  "stats": {
    "power": 50000000,
    "kill_points": 200000000,
    "deads": 5000000,
    "t4_kills": 20000000,
    "t5_kills": 10000000
  },
  "delta": {
    "power": 0,
    "kill_points": 0,
    "deads": 0,
    "t4_kills": 0,
    "t5_kills": 0
  },
  "in_baseline": false,
  "newly_added_to_baseline": true
}
```

## Logging

New player additions are logged:
```
INFO - New player detected: PlayerName (ID: 99999) - Setting as new baseline
INFO - Updated baseline with 3 new players for season season_1
```

Check Railway logs to see when players are added:
```bash
# Railway dashboard → Your service → Deployments → View Logs
```

## Edge Cases Handled

### Case 1: Empty Baseline
```python
if not baseline:
    return error: "Please upload baseline first"
```
System requires baseline to exist before accepting current data.

### Case 2: Duplicate Governor IDs
```python
# Data cleaning removes duplicates, keeping last occurrence
df.drop_duplicates(subset=['governor_id'], keep='last')
```

### Case 3: Player Leaves Then Returns
```
Upload 1: Player in baseline
Upload 2: Player not in current data (ignored)
Upload 3: Player returns → Treated as existing, deltas calculated normally
```

### Case 4: Zero Stats Player
```
New player with 0 power, 0 KP:
- Still added to baseline
- Future uploads will track from zero
```

## Testing

### Test Scenario 1: Add New Player
```bash
1. Upload baseline with 200 players
2. Manually add a new row to Excel file with ID 99999
3. Upload as current data
4. Check leaderboard - new player should have zero deltas
5. Upload again - new player should now show actual deltas
```

### Test Scenario 2: Multiple New Players
```bash
1. Upload baseline
2. Add 5 new players to Excel
3. Upload as current
4. All 5 should have zero deltas
5. Verify baseline count increased by 5
```

### Test Scenario 3: API Verification
```bash
# Check baseline player count
curl https://kd3584-production.up.railway.app/admin/baseline/season_1

# Check if new player has zero deltas
curl https://kd3584-production.up.railway.app/api/player/99999?kvk_season_id=season_1
```

## Future Enhancements

### Possible Additions:
1. **Admin notification** when new players are detected
2. **Baseline history** - track all baseline changes over time
3. **Player removal detection** - mark players who left alliance
4. **Merge duplicate players** - combine stats if same player with new ID
5. **Manual baseline editing** - Admin UI to add/remove players

## Notes

- This feature runs on **every current data upload** (CSV or Excel)
- Database updates are **atomic** - baseline is updated in single operation
- **No breaking changes** - existing functionality remains the same
- **Backward compatible** - works with existing data
- **Performance impact** - Minimal (one extra database update per upload)

---

**Deployed:** January 3, 2026
**Version:** 1.0.0
**Status:** ✅ Production Ready
