# Delete Feature Documentation

## Overview
Added delete functionality to the admin panel to allow removal of incorrect or unwanted data uploads.

## Backend API Endpoints

### 1. Delete Baseline
**Endpoint:** `DELETE /admin/delete/baseline/{kvk_season_id}`

**Description:** Deletes the baseline data for a specific season.

**Warning:** Current data comparisons will fail without a baseline.

**Response:**
```json
{
  "success": true,
  "message": "Baseline deleted for season_1",
  "deleted_file": "baseline.csv",
  "deleted_player_count": 150
}
```

**Error Responses:**
- 404: Baseline not found
- 500: Failed to delete baseline

---

### 2. Delete Current Data
**Endpoint:** `DELETE /admin/delete/current/{kvk_season_id}`

**Description:** Deletes current data snapshot and all upload history entries.

**Note:** Baseline remains intact.

**Response:**
```json
{
  "success": true,
  "message": "Current data and history deleted for season_1",
  "deleted_current": true,
  "deleted_history_count": 5,
  "deleted_file": "current_data.csv"
}
```

**Error Responses:**
- 404: Current data not found

---

### 3. Delete All Data
**Endpoint:** `DELETE /admin/delete/all/{kvk_season_id}`

**Description:** Permanently deletes ALL data for a season (baseline + current + history).

**Warning:** This is irreversible!

**Response:**
```json
{
  "success": true,
  "message": "All data deleted for season_1",
  "deleted_baseline": 1,
  "deleted_current": 1,
  "deleted_history": 5,
  "total_deleted": 7
}
```

**Error Responses:**
- 404: No data found for this season

---

## Frontend Features

### Admin Panel Updates

1. **Delete Baseline Button**
   - Appears in Data Status section when baseline exists
   - Red button with warning confirmation
   - Shows deleted file name and player count on success

2. **Delete Current Data Button**
   - Appears in Data Status section when current data exists
   - Red button with warning confirmation
   - Shows deleted file and history count on success

3. **Danger Zone - Delete All Data**
   - Appears when any data exists
   - Red gradient button in danger zone section
   - Requires TWO confirmations for safety
   - Shows detailed deletion summary on success

### Confirmation Dialogs

#### Delete Baseline
```
⚠️ WARNING: Delete Baseline?

This will remove the baseline reference point.
Current data comparisons will fail without a baseline.

Are you sure you want to delete the baseline?
```

#### Delete Current Data
```
⚠️ WARNING: Delete Current Data?

This will remove:
• Current data snapshot
• All upload history entries

Baseline will remain intact.

Are you sure you want to delete?
```

#### Delete All Data (1st Confirmation)
```
🚨 DANGER: Delete ALL Data?

This will PERMANENTLY delete:
• Baseline data
• Current data
• All upload history

This action CANNOT be undone!

Are you absolutely sure?
```

#### Delete All Data (2nd Confirmation)
```
🚨 FINAL WARNING!

You are about to delete ALL data for season_1.

Type the season ID in your mind to confirm: season_1

Click OK to proceed with PERMANENT deletion.
```

---

## Use Cases

### 1. Wrong File Uploaded (Baseline)
**Scenario:** Admin accidentally uploads wrong baseline CSV

**Solution:**
1. Click "🗑️ Delete Baseline" button
2. Confirm deletion
3. Upload correct baseline file

**Impact:** Current data will show errors until new baseline is uploaded

---

### 2. Wrong File Uploaded (Current)
**Scenario:** Admin uploads wrong current data CSV

**Solution:**
1. Click "🗑️ Delete Current Data" button
2. Confirm deletion
3. Upload correct current data file

**Impact:** Baseline remains intact, only current snapshot is removed

---

### 3. Start Over Completely
**Scenario:** Admin wants to reset entire season due to multiple errors

**Solution:**
1. Click "💥 Delete All Data" button in Danger Zone
2. Confirm TWICE
3. Start fresh with new baseline

**Impact:** All data for the season is permanently deleted

---

## Safety Features

1. **Confirmation Dialogs**
   - All delete operations require user confirmation
   - "Delete All" requires TWO confirmations

2. **Clear Warning Messages**
   - Explains what will be deleted
   - Shows impact of deletion
   - Uses warning emojis (⚠️, 🚨)

3. **Success Feedback**
   - Shows deleted file names
   - Shows count of deleted records
   - Automatic page refresh after deletion

4. **Error Handling**
   - 404 errors if data doesn't exist
   - Clear error messages
   - No partial deletions

---

## Technical Implementation

### Backend Files Modified
- `/backend/app/routes/upload.py` - Added 3 delete endpoints

### Frontend Files Modified
- `/frontend/public/admin.js` - Added 3 delete functions
- `/frontend/public/styles.css` - Added delete button and danger zone styles

### Database Operations
```python
# Delete baseline
await baseline_col.delete_one({"kvk_season_id": kvk_season_id})

# Delete current
await current_col.delete_one({"kvk_season_id": kvk_season_id})
await history_col.delete_many({"kvk_season_id": kvk_season_id})

# Delete all
await baseline_col.delete_many({"kvk_season_id": kvk_season_id})
await current_col.delete_many({"kvk_season_id": kvk_season_id})
await history_col.delete_many({"kvk_season_id": kvk_season_id})
```

---

## Testing

### Manual Testing Steps

1. **Test Delete Baseline:**
   ```bash
   # Upload baseline first
   # Then in admin panel:
   # 1. Click "Delete Baseline"
   # 2. Confirm
   # 3. Verify baseline is gone
   # 4. Check that status shows "No baseline uploaded yet"
   ```

2. **Test Delete Current:**
   ```bash
   # Upload baseline and current data
   # Then in admin panel:
   # 1. Click "Delete Current Data"
   # 2. Confirm
   # 3. Verify current data is gone
   # 4. Verify history is cleared
   # 5. Check that baseline still exists
   ```

3. **Test Delete All:**
   ```bash
   # Upload baseline and current data
   # Then in admin panel:
   # 1. Click "Delete All Data" in danger zone
   # 2. Confirm twice
   # 3. Verify all data is gone
   # 4. Check both status cards show "No data"
   ```

### API Testing with cURL

```bash
# Delete baseline
curl -X DELETE "https://kd3584-production.up.railway.app/admin/delete/baseline/season_1"

# Delete current
curl -X DELETE "https://kd3584-production.up.railway.app/admin/delete/current/season_1"

# Delete all
curl -X DELETE "https://kd3584-production.up.railway.app/admin/delete/all/season_1"
```

---

## Deployment

### Files to Deploy

**Backend (Railway):**
- `backend/app/routes/upload.py`

**Frontend (Vercel):**
- `frontend/public/admin.js`
- `frontend/public/styles.css`

### Deployment Steps
1. Commit changes to git
2. Push to repository
3. Railway will auto-deploy backend
4. Vercel will auto-deploy frontend
5. Test on production URLs

---

## Future Enhancements

1. **Soft Delete** - Archive instead of permanent deletion
2. **Undo Feature** - Allow restoring recently deleted data
3. **Audit Log** - Track who deleted what and when
4. **Backup Before Delete** - Automatic backup creation
5. **Scheduled Deletion** - Delete old data automatically after X days
6. **Individual History Item Delete** - Delete specific upload from history
7. **Export Before Delete** - Download data before deletion

---

## FAQ

**Q: Can I recover deleted data?**
A: No, deletions are permanent. Make sure to export/backup data before deleting.

**Q: What happens if I delete baseline but keep current data?**
A: Current data will remain in database but comparisons will fail. You'll need to upload a new baseline.

**Q: Can I delete individual history entries?**
A: Not yet. Current implementation deletes all history for the season when deleting current data.

**Q: Is there authentication on delete endpoints?**
A: Not currently (security issue noted in main analysis). Should be added in future.

**Q: Can I delete data for specific players?**
A: Not yet. Current implementation only deletes entire snapshots/seasons.

---

## Security Considerations

⚠️ **IMPORTANT:** Delete endpoints currently have NO AUTHENTICATION.

**Recommended fixes:**
1. Add JWT authentication middleware to all `/admin/delete/*` endpoints
2. Add admin role verification
3. Add rate limiting to prevent abuse
4. Add audit logging for all delete operations
5. Consider adding soft delete instead of hard delete

---

## Summary

The delete feature provides admins with the ability to remove incorrect data uploads through a user-friendly interface with appropriate safety measures. The implementation includes:

✅ Three delete endpoints (baseline, current, all)
✅ Confirmation dialogs with clear warnings
✅ Success/error feedback
✅ Automatic UI refresh after deletion
✅ Styled delete buttons with danger zone
✅ Detailed response messages

⚠️ Still needs authentication/authorization on endpoints for production use.
