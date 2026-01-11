# Backend Local Testing Issue

## Problem

Your local virtual environment uses **Python 3.14** which is too new for `pandas` (the data processing library used for Excel/CSV uploads).

Pandas doesn't support Python 3.14 yet, so the backend won't start locally.

## Current Status

✅ **Production is working perfectly** - Railway uses Python 3.11 which supports pandas
✅ **Frontend changes work fine** - You can test frontend locally without backend
✅ **All packages installed** - Everything except pandas is ready

## Solutions

### Option 1: Test Frontend Only (RECOMMENDED FOR NOW)

Since you're only adjusting **font sizes in CSS**, you don't need the backend running:

```bash
cd /Users/punlochan/kd_3584/frontend/public
python3 -m http.server 8080
```

Then open: http://localhost:8080/index.html

**However:** The data won't load (you'll see "Loading leaderboard..." forever) because there's no backend.

**Workaround:** Just check the font sizes by inspecting the table structure in browser DevTools.

### Option 2: Recreate Virtual Environment with Python 3.11

```bash
cd /Users/punlochan/kd_3584/backend

# Remove old venv
rm -rf venv

# Create new venv with Python 3.11 (if you have it installed)
python3.11 -m venv venv

# Activate and install
source venv/bin/activate
pip install -r requirements.txt

# Start backend
./start_backend.sh
```

**Problem:** You might not have Python 3.11 installed.

### Option 3: Install Python 3.11 via Homebrew

```bash
# Install Python 3.11
brew install python@3.11

# Then follow Option 2 above
```

### Option 4: Test on Production Directly

Since font size changes are simple CSS:

1. Edit `frontend/public/styles.css` locally
2. Commit and push to production
3. Check on live site: https://kd3584-production.up.railway.app
4. If you don't like it, revert and push again

## Recommended Approach

For **font size adjustments only**, use **Option 4**:

1. Edit the CSS file (lines documented in guides)
2. Deploy to production with git push
3. Check the result on live site
4. Iterate until you're happy

This is actually faster than local testing since:
- No backend needed for CSS changes
- Railway deploys in ~1-2 minutes
- You can see real data on production
- No Python version conflicts

## Font Size Locations

Edit: `frontend/public/styles.css`

- **Line 500**: Desktop stat values (currently `0.75rem`)
- **Line 454**: Mobile stat values (currently `0.7rem`)
- **Line 1424**: Desktop gained stats (currently `0.75rem`)
- **Line 1429**: Mobile gained stats (currently `0.7rem`)
- **Line 157**: Mobile stats card (currently `1.2rem`)

Try these values:
- Smaller: `0.65rem` or `0.6rem`
- Even smaller: `0.55rem` or `0.5rem`

## Deploy Command

```bash
cd /Users/punlochan/kd_3584
git add frontend/public/styles.css
git commit -m "Adjust stat font sizes"
git push
```

Wait 1-2 minutes, then check: https://kd3584-production.up.railway.app
