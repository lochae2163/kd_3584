# Local Testing & Deployment Guide

## Part 1: Local Testing (Frontend + Backend)

### Step 1: Open Two Terminal Windows

You'll need TWO separate terminal windows:
- **Terminal 1**: For Backend (Python FastAPI)
- **Terminal 2**: For Frontend (Static file server)

---

### Step 2: Start Backend (Terminal 1)

**✨ Easy Method (RECOMMENDED):**

```bash
cd /Users/punlochan/kd_3584
./start_backend.sh
```

**Manual Method:**

```bash
cd /Users/punlochan/kd_3584/backend
/Users/punlochan/kd_3584/backend/venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Note:** All packages are now installed and ready to use!

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Backend is now running at:** http://localhost:8000

**To stop backend:** Press `Ctrl+C`

---

### Step 3: Start Frontend (Terminal 2)

**✨ Easy Method (RECOMMENDED):**

```bash
cd /Users/punlochan/kd_3584
./start_frontend.sh
```

**Manual Method:**

```bash
cd /Users/punlochan/kd_3584/frontend/public
python3 -m http.server 8080
```

**Expected Output:**
```
Serving HTTP on :: port 8080 (http://[::]:8080/) ...
```

**Frontend is now running at:** http://localhost:8080

**To stop frontend:** Press `Ctrl+C`

---

### Step 4: Open in Browser

Open these URLs in your browser:

- **Main Dashboard:** http://localhost:8080/index.html
- **DKP Leaderboard:** http://localhost:8080/contribution.html
- **Admin Panel:** http://localhost:8080/admin.html
- **Backend API:** http://localhost:8000/docs

---

### Step 5: Make Changes to CSS

1. Open the file: `frontend/public/styles.css`
2. Find the lines you want to change (see section below)
3. Save the file
4. **Refresh your browser** (just press F5 or Cmd+R)
5. Changes will show immediately - no need to restart server!

---

## Part 2: Font Size Locations in styles.css

### Desktop Stat Values (Line 500)
```css
.stat-value {
    font-size: 0.75rem;  /* ← Change this */
}
```
**Try:** `0.7rem`, `0.65rem`, or `0.6rem`

---

### Desktop Gained Stats (Line 1424)
```css
.gained-stat {
    font-size: 0.75rem;  /* ← Change this */
}
```
**Try:** Same as stat-value above

---

### Mobile Stat Values (Line 454)
```css
@media (max-width: 768px) {
    .stat-value {
        font-size: 0.7rem;  /* ← Change this */
    }
}
```
**Try:** `0.65rem`, `0.6rem`, or `0.55rem`

---

### Mobile Gained Stats (Line 1429)
```css
@media (max-width: 768px) {
    .gained-stat {
        font-size: 0.7rem !important;  /* ← Change this */
    }
}
```
**Try:** Same as mobile stat-value above

---

### Mobile Stats Card Values (Line 157)
```css
@media (max-width: 500px) {
    .stat-card .value {
        font-size: 1.2rem;  /* ← Change this */
    }
}
```
**Try:** `1rem`, `0.9rem`, or `0.85rem`

---

## Part 3: Testing Mobile View on Desktop

### Chrome/Edge:
1. Press `F12` to open Developer Tools
2. Press `Ctrl+Shift+M` (Windows) or `Cmd+Shift+M` (Mac)
3. Select a mobile device from dropdown (e.g., iPhone 12 Pro)
4. Refresh page to see mobile view

### Firefox:
1. Press `F12` to open Developer Tools
2. Click the phone/tablet icon in top-right
3. Select a mobile device
4. Refresh page

---

## Part 4: Deploy to Production

### Quick Deploy (After Testing Locally)

```bash
# Navigate to project root
cd /Users/punlochan/kd_3584

# Add your changes
git add frontend/public/styles.css

# Commit with message
git commit -m "Adjust stat font sizes"

# Push to deploy
git push
```

### All-in-One Deploy Command

```bash
cd /Users/punlochan/kd_3584 && git add frontend/public/styles.css && git commit -m "Adjust stat font sizes" && git push
```

---

## Part 5: Check Deployment Status

### Wait 1-2 minutes, then visit:
- **Production Site:** https://kd3584-production.up.railway.app

### Check Git Status:
```bash
git status
git log -1
```

---

## Part 6: Troubleshooting

### Problem: Backend won't start
**Solution:**
```bash
# Make sure you're in backend folder
cd /Users/punlochan/kd_3584/backend

# Check if virtual environment exists
ls venv/

# If venv doesn't exist, create it:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### Problem: Frontend shows old version
**Solution:**
1. Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
2. Or clear browser cache
3. Or open in incognito/private window

---

### Problem: Can't connect to backend
**Check:**
1. Backend is running in Terminal 1
2. No error messages in backend terminal
3. Backend URL is correct: http://localhost:8000

---

### Problem: Port already in use
**Solution:**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 8080
lsof -ti:8080 | xargs kill -9
```

---

## Part 7: Stop Everything

### Stop Backend (Terminal 1):
Press `Ctrl+C`

### Stop Frontend (Terminal 2):
Press `Ctrl+C`

### Deactivate Virtual Environment (if active):
```bash
deactivate
```

---

## Quick Reference: Font Sizes

| Size | Use Case |
|------|----------|
| 0.55rem | Very very small |
| 0.6rem | Very small |
| 0.65rem | Small |
| 0.7rem | Small-medium (current mobile) |
| 0.75rem | Medium-small (current desktop) |
| 0.8rem | Medium |
| 0.85rem | Medium-large (mobile player names) |
| 0.9rem | Large (desktop player names) |
| 1rem | Standard |
| 1.2rem | Large (stats cards mobile) |

---

## Recommended Starting Point

Try these values first:

### For Table Stats:
- **Desktop:** `0.65rem` or `0.7rem`
- **Mobile:** `0.6rem` or `0.65rem`

### For Stats Cards:
- **Mobile:** `1rem` or `0.9rem`

---

## Need Help?

If something doesn't work:
1. Check both terminals for error messages
2. Make sure both servers are running
3. Try hard refresh in browser
4. Check the troubleshooting section above
