# File Date Feature - Using Excel Download Date

## Overview

The system now uses the **download date from the Excel file** instead of the upload timestamp. This ensures the dates shown in the leaderboard reflect when the data was actually captured from the game, not when you uploaded it.

## How It Works

### Date Location in Excel File

The Hero Scrolls Kingdom Scanner Excel files contain the download date in the **Summary sheet**:
- **Location:** Row 2, Column F (6th column)
- **Format:** `2026-01-05 17:12 UTC`

### Automatic Extraction

When you upload an Excel file:

1. **Backend reads Summary sheet** - Extracts date from Row 2, Column F
2. **Parses the date** - Converts "YYYY-MM-DD HH:MM UTC" to ISO format
3. **Uses file date** - Stores this date as the timestamp for:
   - Baseline uploads
   - Current data uploads
   - Upload history entries

### Fallback Behavior

If the date cannot be extracted from the Excel file:
- **Warning logged:** "File date not found in Excel, using upload time"
- **Fallback:** Uses the actual upload time (current server time)
- **System continues working** - No errors, just uses upload time instead

## What Changed

### Before (Old Behavior)
```javascript
// Timestamp = when you uploaded the file
baseline.timestamp = "2026-01-11 02:30:00"  // Upload time
```

### After (New Behavior)
```javascript
// Timestamp = when data was downloaded from game
baseline.timestamp = "2026-01-05 17:12:00"  // File date from Excel
```

## Where This Applies

### ✅ Excel Uploads
- Baseline uploads via admin panel
- Current data uploads via admin panel
- Upload history records

### ❌ CSV Uploads
CSV files don't contain the download date, so they still use upload time.

## Benefits

1. **Accurate Timeline** - See when data was actually captured from the game
2. **Historical Tracking** - Upload old files and maintain correct chronology
3. **No Manual Entry** - Date is automatically extracted, no extra work
4. **Consistent Records** - All Excel uploads use file date consistently

## Example Scenario

**You download data from the game on January 5 at 5:12 PM UTC:**
- Hero Scrolls creates Excel file with date: `2026-01-05 17:12 UTC`

**You upload the file to the tracker on January 11:**
- Old system would show: **January 11** (wrong - that's when you uploaded it)
- New system shows: **January 5, 5:12 PM** (correct - when data was captured)

## Frontend Display

The timestamp is displayed in:
1. **Leaderboard page** - "Last updated: [date]"
2. **Admin panel** - Upload history list
3. **API responses** - Timestamp field in JSON

The date will automatically use the file date for all Excel uploads going forward.

## Technical Details

### Code Changes

**File:** `backend/app/ml/data_model.py`
```python
# Extract date from Summary sheet
wb = openpyxl.load_workbook(BytesIO(excel_bytes))
if 'Summary' in wb.sheetnames:
    ws = wb['Summary']
    date_cell = ws.cell(2, 6).value  # Row 2, Column F
    if date_cell and 'UTC' in str(date_cell):
        date_str = date_cell.replace(' UTC', '').strip()
        file_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M').isoformat()
```

**File:** `backend/app/services/ml_service.py`
```python
# Use file_date if available
timestamp = result.get('file_date')
if timestamp:
    timestamp = datetime.fromisoformat(timestamp)
else:
    timestamp = datetime.utcnow()  # Fallback
```

### Database Schema

The timestamp field in all documents now contains the file date:

```javascript
{
  "kvk_season_id": "season_6",
  "file_name": "kingdom_scan_123.xlsx",
  "timestamp": "2026-01-05T17:12:00",  // ← File date, not upload time
  "players": [...]
}
```

## Testing

To verify this works:

1. Upload an Excel file from Hero Scrolls
2. Check the admin panel upload history
3. Verify the timestamp matches the date in the Excel Summary sheet (Row 2, Col F)
4. Check the leaderboard "Last updated" date

## Future Enhancements

Potential improvements:
- Extract date from CSV filenames if they follow a pattern
- Allow manual date override in admin panel
- Show both file date and upload date in UI
- Warn if file date is in the future or very old

## Notes

- Date extraction happens automatically, no configuration needed
- Works with all Hero Scrolls Excel formats
- Backward compatible - old uploads keep their upload timestamps
- New uploads will use file date automatically
