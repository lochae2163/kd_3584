# Quick Start: Excel Upload

## 🚀 You can now upload Excel files directly!

No more CSV conversion needed! Just upload the Hero Scrolls Excel file directly.

---

## How to Use

### Step 1: Download from Hero Scrolls
1. Open Hero Scrolls Kingdom Scanner
2. Scan Kingdom 3584
3. Download the Excel file (`.xlsx`)

You'll get a file like: `kingdom_scan_742871269048975389_1766002874_3851.xlsx`

### Step 2: Upload to Tracker

#### Local Development
1. Open admin panel: [http://localhost:5500/admin.html](http://localhost:5500/admin.html)
2. Click "Select File (CSV or Excel)"
3. Choose your Excel file
4. Click "Upload Baseline" or "Upload Current Data"
5. ✅ Done!

#### Production
1. Open admin panel: [https://your-production-url/admin.html](https://your-production-url/admin.html)
2. Click "Select File (CSV or Excel)"
3. Choose your Excel file
4. Click "Upload Baseline" or "Upload Current Data"
5. ✅ Done!

---

## What Happens Automatically

✅ **Finds the correct sheet** - Looks for "3584" or "Rolled Up 3584"
✅ **Maps all columns** - Converts Hero Scrolls format to tracker format
✅ **Cleans the data** - Removes commas, fixes numbers
✅ **Validates everything** - Makes sure all required fields exist
✅ **Shows success** - Tells you which sheet was used

---

## Example Success Message

```
✅ Baseline saved with 205 players from Excel

Sheet used: 3584
File: kingdom_scan_742871269048975389_1766002874_3851.xlsx
Players: 205
```

---

## Still Works: CSV Upload

Don't worry! CSV upload still works exactly as before:
- Upload any CSV file
- Same format as always
- No changes needed

You can use **both** CSV and Excel - whatever you prefer!

---

## Troubleshooting

### "Could not find data sheet"
**Problem:** The Excel file doesn't have a sheet named "3584"
**Solution:** Make sure you're uploading the correct Hero Scrolls file

### "Missing required columns"
**Problem:** The Excel sheet is missing some data columns
**Solution:** Make sure the Excel file has: Governor ID, Governor Name, Power, Deads, Kill Points, T4 Kills, T5 Kills

### "File type not supported"
**Problem:** You uploaded a file that's not CSV or Excel
**Solution:** Upload a `.csv`, `.xlsx`, or `.xls` file

---

## Benefits

### Before (CSV)
1. Download Excel from Hero Scrolls ⏱️
2. Open in Excel/Google Sheets ⏱️
3. Export as CSV ⏱️
4. Upload CSV to tracker ⏱️

**Total: 5-10 minutes**

### Now (Excel)
1. Download Excel from Hero Scrolls ⏱️
2. Upload directly to tracker ⏱️

**Total: 1 minute**

---

## Need Help?

Check the full documentation:
- [Excel Upload Feature Guide](EXCEL_UPLOAD_FEATURE.md)
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md)

---

**That's it! Just upload your Hero Scrolls Excel file directly. No conversion needed! 🎉**
