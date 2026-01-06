# Quick Start Guide

## ✅ Fixed! Backend is ready to use

All packages are installed. You can now start testing locally.

## Start Both Servers (2 Terminals)

### Terminal 1 - Backend:
```bash
cd /Users/punlochan/kd_3584
./start_backend.sh
```

**If you get "Address already in use" error:**
```bash
lsof -ti:8000 | xargs kill -9
./start_backend.sh
```

### Terminal 2 - Frontend:
```bash
cd /Users/punlochan/kd_3584
./start_frontend.sh
```

## Open in Browser

- **Main Dashboard:** http://localhost:8080/index.html
- **DKP Leaderboard:** http://localhost:8080/contribution.html
- **Admin Panel:** http://localhost:8080/admin.html
- **API Docs:** http://localhost:8000/docs

## Change Font Sizes

Edit this file: `frontend/public/styles.css`

**Desktop stat values:** Line 504
```css
font-size: 0.75rem;  /* Change this number */
```

**Mobile stat values:** Line 454
```css
font-size: 0.7rem;  /* Change this number */
```

**After changing, just refresh browser (F5)**

## Deploy to Production

```bash
cd /Users/punlochan/kd_3584
git add frontend/public/styles.css
git commit -m "Adjust font sizes"
git push
```

Wait 1-2 minutes, then check: https://kd3584-production.up.railway.app

## Stop Servers

Press `Ctrl+C` in each terminal window

---

For detailed guide, see: [LOCAL_TESTING_GUIDE.md](LOCAL_TESTING_GUIDE.md)
