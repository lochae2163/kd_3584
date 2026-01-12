# Fight Period Tracking - Real KP vs Trade KP

## 📋 Feature Overview

This feature allows admins to track **real combat KP** (Kill Points gained during actual fights) separately from **trade KP** (Kill Points gained through player-to-player trading).

### Problem Statement
In Rise of Kingdoms KvK, players can gain KP in two ways:
1. **Real fights**: Killing enemy troops (generates both KP and T4/T5 kills)
2. **Trading**: Trading kills with other players (generates KP but no actual T4/T5 kills)

We need to exclude trade KP from rankings to accurately measure real combat contribution.

### Solution Approach
Instead of trying to detect trades algorithmically, **admins manually mark fight periods** (when real fighting occurs). The system then calculates KP gained only during these periods.

---

## 🏗️ Architecture

### Database Schema

**Collection: `fight_periods`**
```javascript
{
  "season_id": "season_6",
  "fight_number": 1,
  "fight_name": "Pass 1 - Kingdom 1234",
  "start_time": "2025-12-25T10:00:00",
  "end_time": "2025-12-28T23:59:59",
  "status": "completed",  // upcoming, active, completed
  "description": "First major battle of KvK 6",
  "created_at": "2026-01-12T10:05:24",
  "updated_at": "2026-01-12T10:05:24",
  "created_by": "lochan3584"
}
```

### API Endpoints

#### Public Endpoints (No Auth)
- `GET /api/fight-periods/{season_id}` - List all fight periods
- `GET /api/fight-periods/{season_id}/{fight_number}` - Get specific fight

#### Admin Endpoints (Auth Required)
- `POST /admin/fight-periods` - Create new fight period
- `PUT /admin/fight-periods/{season_id}/{fight_number}` - Update fight
- `POST /admin/fight-periods/{season_id}/{fight_number}/end` - Mark fight as ended
- `DELETE /admin/fight-periods/{season_id}/{fight_number}` - Delete fight

---

## 📁 Files Created/Modified

### New Files
1. **`backend/app/models/fight_period.py`** - Pydantic models
2. **`backend/app/services/fight_period_service.py`** - Business logic
3. **`backend/app/routes/fight_periods.py`** - API endpoints

### Modified Files
1. **`backend/app/cache.py`** - Added fight_periods cache key
2. **`backend/app/main.py`** - Registered fight period routers

---

## 🧪 Testing

### Test 1: Create Fight Period
```bash
# Login as admin
curl -X POST 'http://localhost:8000/admin/login' \
  -H 'Content-Type: application/json' \
  -d '{"username": "lochan3584", "password": "VungkXU2O6up7Z8h!"}'

# Response:
# {"access_token": "eyJ...", "token_type": "bearer"}

# Create fight period
curl -X POST 'http://localhost:8000/admin/fight-periods' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'Content-Type: application/json' \
  -d '{
    "season_id": "season_6",
    "fight_number": 1,
    "fight_name": "Pass 1 - Kingdom 1234",
    "start_time": "2025-12-25T10:00:00",
    "end_time": "2025-12-28T23:59:59",
    "description": "First major battle of KvK 6"
  }'

# Response:
# {
#   "success": true,
#   "message": "Fight period created: Pass 1 - Kingdom 1234",
#   "fight_period": {...}
# }
```

### Test 2: List Fight Periods
```bash
curl 'http://localhost:8000/api/fight-periods/season_6'

# Response:
# {
#   "success": true,
#   "season_id": "season_6",
#   "count": 1,
#   "fight_periods": [...]
# }
```

---

## 🔄 Next Steps (Phase 2)

### 1. Calculate Real Fight KP
Update `ml_service.py` to calculate KP gained during fight periods:

```python
async def calculate_real_fight_kp(season_id: str, governor_id: str):
    """
    Calculate KP gained only during fight periods

    Logic:
    1. Get all fight periods for season
    2. For each fight period:
       - Find upload before fight start
       - Find upload after fight end
       - Calculate KP delta
    3. Sum all deltas = Real Fight KP
    4. Total KP - Real Fight KP = Trade KP
    """
    fight_periods = await fight_period_service.get_fight_periods(season_id)
    uploads = await get_uploads_history(season_id)

    real_kp = 0
    for fight in fight_periods:
        before = find_upload_before(uploads, fight.start_time)
        after = find_upload_after(uploads, fight.end_time)
        real_kp += after.kp - before.kp

    return {
        "real_fight_kp": real_kp,
        "trade_kp": total_kp - real_kp,
        "fight_count": len(fight_periods)
    }
```

### 2. Update Leaderboard
Modify leaderboard response to include:
```json
{
  "governor_id": "12345",
  "governor_name": "Player1",
  "total_kp_gained": 500000000,
  "real_fight_kp_gained": 450000000,
  "trade_kp_gained": 50000000,
  "fight_kp_percentage": 90.0
}
```

### 3. Frontend Admin Panel
Add UI for managing fight periods:
- List all fights for current season
- Create new fight button
- Edit/Delete existing fights
- Visual timeline showing fights vs trading periods

### 4. Frontend Leaderboard
Add column toggles:
- Show/hide Total KP
- Show/hide Real Fight KP
- Show/hide Trade KP
- Sort by any KP type

---

## 💡 Usage Example

### Timeline Visualization
```
KvK Season 6 Timeline:
├─ Dec 23 - Baseline Upload
├─ Dec 25-28 [FIGHT 1] Pass 1 vs Kingdom 1234 ✓
├─ Dec 29-Jan 1 [TRADING] (excluded)
├─ Jan 2-5 [FIGHT 2] Pass 2 vs Kingdom 5678 ✓
├─ Jan 6-8 [TRADING] (excluded)
├─ Jan 9-11 [FIGHT 3] Final Battle vs Kingdom 9012 ✓
└─ Jan 12 - Final Upload

Real Fight KP = KP gained during Fight 1 + Fight 2 + Fight 3
Trade KP = Total KP - Real Fight KP
```

### Admin Workflow
1. **Before KvK**: Admin creates season (already implemented)
2. **Fight Starts**: Admin creates fight period with start_time
3. **Fight Ends**: Admin updates fight period with end_time
4. **Between Fights**: No action needed (trading periods auto-excluded)
5. **After KvK**: Leaderboard shows both Real KP and Total KP

---

## ✅ Phase 1 Complete

- ✅ Database models
- ✅ Service layer with caching
- ✅ API endpoints (public + admin)
- ✅ Validation logic
- ✅ Integration with main app
- ✅ Basic testing

## 🚧 Phase 2 TODO

- ⏳ ML service KP calculation logic
- ⏳ Leaderboard endpoint updates
- ⏳ Admin panel UI
- ⏳ Frontend leaderboard updates
- ⏳ End-to-end testing with real data

---

## 🎯 Success Metrics

Once Phase 2 is complete:
1. Admins can easily mark fight periods in <30 seconds
2. Real fight KP calculations are accurate within 1%
3. Leaderboard updates reflect fight periods within 1 minute (cache refresh)
4. Players can see their combat contribution vs total contribution
5. System handles 10+ fight periods per season without performance issues

---

## 📚 Technical Notes

### Cache Strategy
- Fight periods cached for 5 minutes
- Invalidated on create/update/delete
- Leaderboard cache invalidated when fight periods change

### Status Auto-Management
Fight status automatically determined based on timestamps:
- `upcoming`: start_time > now
- `active`: start_time <= now < end_time
- `completed`: end_time <= now OR manually marked complete

### Validation Rules
- Fight numbers must be unique per season
- start_time must be before end_time
- Cannot create overlapping fights (future enhancement)
- Only admins can create/modify/delete fights

---

*Created: 2026-01-12*
*Feature: Fight Period Tracking*
*Status: Phase 1 Complete ✅*
