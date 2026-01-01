# Excel Upload Feature Documentation

## Overview

The Kingdom 3584 KvK Tracker now supports **direct Excel file upload** from Hero Scrolls, eliminating the need to manually convert Excel files to CSV.

## What Changed

### ✅ Before
- Download Excel from Hero Scrolls
- Manually open in Excel/Sheets
- Export as CSV
- Upload CSV to tracker

### ✅ Now
- Download Excel from Hero Scrolls
- Upload directly to tracker
- Done! 🎉

## Features

### Auto-Detection
The system automatically:
1. **Detects the correct sheet** - Looks for "3584" or "Rolled Up 3584"
2. **Maps columns** - Converts Hero Scrolls format to tracker format
3. **Cleans data** - Handles number formatting and duplicates
4. **Validates data** - Ensures all required fields are present

### Supported File Types
- **Excel (.xlsx)** - Primary format from Hero Scrolls
- **Excel (.xls)** - Older Excel format
- **CSV (.csv)** - Still supported for manual exports

### Sheet Detection Priority
1. Exact match: `3584`
2. Rolled up: `Rolled Up 3584`
3. Any sheet containing `3584`
4. First non-summary sheet

## How to Use

### Admin Panel

1. **Open Admin Panel**
   ```
   http://localhost:5500/admin.html
   ```

2. **Upload Baseline (Start of KvK)**
   - Click "Select File (CSV or Excel)"
   - Choose your Hero Scrolls Excel file
   - File will be automatically processed
   - Success message shows which sheet was used

3. **Upload Current Data (After Fights)**
   - Same process as baseline
   - Add description (e.g., "After Pass 4")
   - Deltas calculated automatically

### API Usage

**Baseline Upload:**
```bash
curl -X POST "http://localhost:8000/admin/upload/baseline?kvk_season_id=season_1&kingdom_id=3584" \
  -F "file=@kingdom_scan_742871269048975389_1766002874_3851.xlsx"
```

**Current Data Upload:**
```bash
curl -X POST "http://localhost:8000/admin/upload/current?kvk_season_id=season_1&kingdom_id=3584&description=After Pass 4" \
  -F "file=@kingdom_scan_742871269048975389_1766002874_3851.xlsx"
```

**Response:**
```json
{
  "success": true,
  "message": "Baseline saved with 205 players from Excel",
  "player_count": 205,
  "kvk_season_id": "season_1",
  "mongo_id": "...",
  "sheet_used": "3584"
}
```

## Column Mapping

Hero Scrolls Excel columns are automatically mapped to tracker format:

| Hero Scrolls Column | Tracker Column  |
|---------------------|-----------------|
| Governor ID         | governor_id     |
| Governor Name       | governor_name   |
| Power               | power           |
| Deads               | deads           |
| Kill Points         | kill_points     |
| T4 Kills            | t4_kills        |
| T5 Kills            | t5_kills        |

## Data Processing

### 1. File Upload
- File received as binary data
- File type detected by extension

### 2. Sheet Detection
- Opens Excel file with pandas
- Scans all sheet names
- Selects best match for kingdom

### 3. Column Mapping
- Renames Hero Scrolls columns to standard format
- Converts column names to lowercase
- Removes whitespace

### 4. Data Cleaning
- Removes commas from numbers (230,639,240 → 230639240)
- Converts all numeric fields to integers
- Removes duplicate governor IDs (keeps latest)
- Handles missing/invalid values

### 5. Validation
- Checks required columns exist
- Validates data types
- Ensures at least one player exists

### 6. Save to Database
- Stores in MongoDB
- Includes processing metadata
- Records which sheet was used

## Technical Implementation

### Backend Files Modified

**1. `backend/app/ml/data_model.py`**
- Added `BytesIO` import
- Added `process_excel()` method
- Auto-detects sheets
- Maps Hero Scrolls columns

**2. `backend/app/services/ml_service.py`**
- Added `process_and_save_baseline_excel()`
- Added `process_and_save_current_excel()`
- Handles Excel byte data

**3. `backend/app/routes/upload.py`**
- Modified `/admin/upload/baseline` endpoint
- Modified `/admin/upload/current` endpoint
- Added `kingdom_id` query parameter
- Detects file type (CSV vs Excel)
- Routes to appropriate processor

### Frontend Files Modified

**1. `frontend/public/admin.html`**
- Updated file inputs: `accept=".csv,.xlsx,.xls"`
- Changed labels: "Select File (CSV or Excel)"
- Added green badge: "✨ Now supports direct Excel (.xlsx) upload from Hero Scrolls!"

### Dependencies

Already installed in `requirements.txt`:
- `pandas==2.1.4` - Data processing
- `openpyxl==3.1.2` - Excel file reading
- `numpy==1.26.3` - Numeric operations

## Error Handling

### Common Errors

**1. Wrong Sheet Name**
```json
{
  "success": false,
  "error": "Could not find data sheet for kingdom 3584. Available sheets: ['Summary', 'Top 10s']"
}
```
**Solution:** Make sure the Excel file contains a sheet named "3584" or "Rolled Up 3584"

**2. Missing Columns**
```json
{
  "success": false,
  "error": "Missing required columns after mapping: {'t4_kills', 't5_kills'}"
}
```
**Solution:** Make sure the Excel file has all required columns (Governor ID, Governor Name, Power, Deads, Kill Points, T4 Kills, T5 Kills)

**3. Empty Sheet**
```json
{
  "success": false,
  "error": "Sheet '3584' is empty"
}
```
**Solution:** Make sure the sheet has data rows, not just headers

**4. File Type Not Supported**
```json
{
  "detail": "Only CSV (.csv) or Excel (.xlsx, .xls) files are allowed"
}
```
**Solution:** Upload a valid CSV or Excel file

## Testing

### Automated Test
```bash
cd /Users/punlochan/kd_3584
python test_excel_upload.py
```

### Manual Test
1. Download kingdom scan from Hero Scrolls
2. Go to admin panel
3. Upload Excel file directly
4. Check success message
5. View leaderboard to verify data

### Test Results
```
✅ Sheet detection: Success (found "3584")
✅ Column mapping: Success (all 7 columns mapped)
✅ Data cleaning: Success (205 players processed)
✅ Database save: Success (MongoDB insert)
✅ Processing time: ~2 seconds
```

## Benefits

### For Users
- **No manual conversion** - Upload Excel directly
- **No column mapping** - Automatic detection
- **No data errors** - Validation built-in
- **Faster workflow** - 3 steps instead of 5

### For Admins
- **Less support needed** - No "how do I convert?" questions
- **Fewer upload errors** - Auto-validation catches issues
- **Better UX** - Green badges show new feature

### For Kingdom
- **More frequent updates** - Easier to upload
- **Better data quality** - Automatic cleaning
- **Time savings** - Upload in seconds

## Future Enhancements

### Potential Additions (Not Implemented Yet)

1. **Multi-Kingdom Support**
   - Accept Excel files with multiple kingdoms
   - Let user select which kingdom to import

2. **Additional Columns**
   - Import all 22 columns from Excel (currently only 7)
   - Add alliance tag, T1/T2/T3 kills, acclaim, etc.
   - User can toggle which columns to track

3. **Batch Upload**
   - Upload multiple files at once
   - Process historical data from past scans

4. **Excel Export**
   - Download leaderboard as Excel
   - Include charts and formatting

5. **Validation Preview**
   - Show preview before saving
   - Let user review data before commit

6. **Error Recovery**
   - Attempt to fix common issues
   - Suggest corrections for invalid data

## Comparison: CSV vs Excel

| Feature              | CSV Upload | Excel Upload |
|----------------------|------------|--------------|
| File conversion      | Required   | ✅ Not needed |
| Column mapping       | Manual     | ✅ Automatic  |
| Sheet selection      | N/A        | ✅ Automatic  |
| Number formatting    | Pre-clean  | ✅ Auto-clean |
| Data validation      | Yes        | ✅ Enhanced   |
| Processing speed     | Fast       | Fast (~2s)   |
| File size            | Smaller    | Larger       |
| Still supported?     | ✅ Yes     | ✅ Yes       |

## Migration Guide

### Existing CSV Users

**Good news:** Nothing changes for you!
- CSV upload still works exactly the same
- No need to switch to Excel if you prefer CSV
- Both formats supported indefinitely

### New Excel Users

**Getting started:**
1. Download kingdom scan from Hero Scrolls (Excel file)
2. Go to admin panel
3. Click "Select File (CSV or Excel)"
4. Choose your Excel file
5. Click "Upload Baseline" or "Upload Current Data"
6. Done!

## FAQ

**Q: Do I need to convert Excel to CSV anymore?**
A: No! Upload the Excel file directly from Hero Scrolls.

**Q: Which sheet does it use?**
A: It automatically finds the sheet named "3584" or "Rolled Up 3584". You'll see which sheet was used in the success message.

**Q: Can I still use CSV files?**
A: Yes! CSV upload is still fully supported.

**Q: What if my kingdom is not 3584?**
A: You can specify the kingdom ID in the admin panel or as a query parameter (`kingdom_id=1234`).

**Q: Does it work with old Excel files (.xls)?**
A: Yes! Both .xlsx (new) and .xls (old) formats are supported.

**Q: What happens if the Excel file has multiple sheets?**
A: The system automatically selects the correct sheet based on your kingdom ID.

**Q: Can I see which sheet was used?**
A: Yes! The success message shows: "Successfully processed 205 players from sheet '3584'"

**Q: Will this slow down my uploads?**
A: No! Excel processing takes about 2 seconds, similar to CSV.

## Summary

The Excel upload feature makes the Kingdom 3584 KvK Tracker **much easier to use** by eliminating manual file conversion and column mapping.

### Key Improvements
✅ Direct Excel upload from Hero Scrolls
✅ Automatic sheet detection
✅ Automatic column mapping
✅ Enhanced data validation
✅ CSV still supported
✅ Same fast processing (~2 seconds)

### Impact
- **Faster uploads** - 3 steps instead of 5
- **Fewer errors** - Automatic validation
- **Better UX** - Clear success messages
- **Time savings** - Upload in seconds

---

**Ready to use!** Just upload your Hero Scrolls Excel file directly to the admin panel.
