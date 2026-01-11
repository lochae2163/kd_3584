# Migrate Old Dates - Update Database Timestamps

## Overview

This script updates existing database records to use the correct file dates from Excel files instead of upload times.

## What It Does

1. Scans your database for all baseline, current_data, and upload_history records
2. For each Excel file upload, finds the matching file on your computer
3. Extracts the date from the Excel Summary sheet (Row 2, Column F)
4. Updates the timestamp in the database

## Requirements

- Original Excel files saved on your computer
- Python with motor, openpyxl installed (already have these)
- MongoDB connection (your .env file)

## Usage

### Step 1: Organize Your Excel Files

Put all your original Excel files in one folder, for example:
```
/Users/punlochan/kd_3584/excel_files/
  ├── kingdom_scan_day1.xlsx
  ├── kingdom_scan_day5.xlsx
  ├── kingdom_scan_day10.xlsx
  └── ...
```

### Step 2: Test Run (Dry Run)

First, run with `--dry-run` to preview what would be updated:

```bash
cd /Users/punlochan/kd_3584/backend

python3 update_existing_timestamps.py \
  --excel-dir /Users/punlochan/kd_3584/excel_files \
  --dry-run
```

This will show you:
- Which files will be updated
- What the old and new timestamps are
- Any files that can't be found or processed
- **No changes are made to the database**

### Step 3: Update Database (Live Run)

If the dry run looks good, run without `--dry-run`:

```bash
cd /Users/punlochan/kd_3584/backend

python3 update_existing_timestamps.py \
  --excel-dir /Users/punlochan/kd_3584/excel_files
```

This will actually update your database.

## Example Output

```
======================================================================
DATABASE TIMESTAMP UPDATE SCRIPT
======================================================================
Excel directory: /Users/punlochan/kd_3584/excel_files
Mode: DRY RUN (no changes)
======================================================================

Found 15 Excel files in directory

📊 Checking BASELINES collection...
----------------------------------------------------------------------

1. Season: season_6, File: kingdom_scan_123.xlsx
  ✅ Extracted date: 2025-12-17 20:21:00
  Current timestamp: 2026-01-05 10:30:00
  New timestamp: 2025-12-17 20:21:00
  🔍 Would update (dry run)

📊 Checking CURRENT_DATA collection...
----------------------------------------------------------------------

1. Season: season_6, File: kingdom_scan_456.xlsx
  ✅ Extracted date: 2026-01-05 17:12:00
  Current timestamp: 2026-01-11 08:45:00
  New timestamp: 2026-01-05 17:12:00
  🔍 Would update (dry run)

======================================================================
📈 SUMMARY
======================================================================
Baselines checked: 1
Baselines updated: 1

Current data checked: 3
Current data updated: 3

History records checked: 5
History records updated: 5

⚠️  Files not found: 2
❌ Date extraction failed: 0
======================================================================

🔍 This was a DRY RUN - no changes were made
Run without --dry-run to actually update the database
```

## What If Files Are Missing?

If the script can't find an Excel file:
- It will show: `⚠️ Excel file not found in directory`
- That record won't be updated
- The script continues with other files

**Options:**
1. Find the missing file and add it to the directory
2. Leave it as-is (that record keeps its upload timestamp)
3. Re-upload that file through admin panel (gets new timestamp automatically)

## Important Notes

### ✅ Safe to Run
- Dry run mode shows what will happen before making changes
- Only updates Excel-based uploads (CSV uploads are skipped)
- Doesn't delete or modify player data, only timestamps
- Can be run multiple times safely

### ⚠️ Backup Recommended
Before running the live update, you can backup your database:
```bash
# MongoDB Atlas backup (via UI)
# Or export specific collections
```

### 🔄 After Running
- Refresh your admin panel and leaderboard pages
- Dates should now show the correct file dates
- Upload history will show accurate timeline

## Troubleshooting

### Error: "No module named 'motor'"
```bash
pip install motor openpyxl python-dotenv
```

### Error: "MONGODB_URL not found"
Make sure you're running from the backend folder:
```bash
cd /Users/punlochan/kd_3584/backend
```

### Files Not Found
Make sure the file names in the database match the file names on disk exactly:
- Case sensitive: `Kingdom_Scan.xlsx` ≠ `kingdom_scan.xlsx`
- Check spaces and special characters

## Alternative: Re-Upload Files

If you don't want to use the script, you can simply:
1. Go to admin panel
2. Upload each Excel file again
3. System automatically extracts correct dates

The script is faster if you have many files to update.

## Questions?

**Q: Will this affect my players' data?**
A: No, only timestamps are updated. Player stats, deltas, and ranks remain unchanged.

**Q: What if I don't have the original files?**
A: Those records will keep their upload timestamps. New uploads will use correct dates.

**Q: Can I undo this?**
A: Not automatically, but you could manually update timestamps in MongoDB if needed.

**Q: Do I need to run this regularly?**
A: No, only once to fix existing data. New uploads automatically use correct dates.
