# Local Development Guide

## 🚀 Your Application is Now Running!

### Running Services

✅ **Backend API** - `http://localhost:8000`
- FastAPI server with hot reload
- MongoDB connection to Atlas
- All delete endpoints active

✅ **Frontend** - `http://localhost:5500`
- Static file server
- Auto-detects localhost and uses local backend
- All pages available

### 📱 Available Pages

| Page | URL | Description |
|------|-----|-------------|
| **Main Leaderboard** | http://localhost:5500/ | View player rankings and stats |
| **Admin Panel** | http://localhost:5500/admin.html | Upload data & delete features |
| **Player Details** | http://localhost:5500/player.html?id={ID} | Individual player page |

### 🎯 Testing the Delete Feature

1. **Open Admin Panel:**
   ```
   http://localhost:5500/admin.html
   ```

2. **View Current Data Status:**
   - You'll see two cards: Baseline & Current Data
   - If data exists, delete buttons will appear

3. **Test Delete Baseline:**
   - Click "🗑️ Delete Baseline"
   - Confirm the warning
   - Watch the page refresh automatically

4. **Test Delete Current:**
   - Click "🗑️ Delete Current Data"
   - Confirm the warning
   - History will be cleared too

5. **Test Delete All (Danger Zone):**
   - Scroll to red "Danger Zone" section
   - Click "💥 Delete All Data"
   - Confirm TWICE
   - All data removed

### 🔧 Development Features

**Auto API Detection:**
- JavaScript files now auto-detect localhost
- Uses `http://localhost:8000` when running locally
- Uses production URL when deployed

**Hot Reload:**
- Backend: Changes reload automatically (uvicorn --reload)
- Frontend: Refresh browser to see changes

### 📊 API Endpoints Available

**Public:**
- GET http://localhost:8000/ - Health check
- GET http://localhost:8000/api/leaderboard
- GET http://localhost:8000/api/player/{id}
- GET http://localhost:8000/api/stats/summary

**Admin:**
- POST http://localhost:8000/admin/upload/baseline
- POST http://localhost:8000/admin/upload/current
- DELETE http://localhost:8000/admin/delete/baseline/{season}
- DELETE http://localhost:8000/admin/delete/current/{season}
- DELETE http://localhost:8000/admin/delete/all/{season}

**Test:**
- GET http://localhost:8000/docs - Interactive API docs (FastAPI Swagger)

### 🛠️ Commands Reference

**Start Backend:**
```bash
cd /Users/punlochan/kd_3584/backend
uvicorn app.main:app --reload --port 8000
```

**Start Frontend:**
```bash
cd /Users/punlochan/kd_3584/frontend/public
python -m http.server 5500
```

**Stop Servers:**
```bash
# Find process IDs
ps aux | grep -E "uvicorn|http.server" | grep -v grep

# Kill by PID (replace XXXX with actual PID)
kill XXXX
```

**Check if Running:**
```bash
# Backend
curl http://localhost:8000/

# Frontend
curl http://localhost:5500/ | head -20
```

### 🌐 Interactive API Documentation

FastAPI provides automatic interactive docs:

**Swagger UI:**
```
http://localhost:8000/docs
```

**ReDoc:**
```
http://localhost:8000/redoc
```

You can test all API endpoints directly from the browser!

### 📝 Making Changes

**Frontend Changes:**
1. Edit files in `frontend/public/`
2. Refresh browser (Cmd+R)
3. Changes appear immediately

**Backend Changes:**
1. Edit files in `backend/app/`
2. Save file
3. Uvicorn auto-reloads
4. Check terminal for reload confirmation

**CSS Changes:**
1. Edit `frontend/public/styles.css`
2. Hard refresh (Cmd+Shift+R)
3. Styles update

### 🎨 What's New - Delete Features

The admin panel now has **three delete options**:

1. **Delete Baseline Only**
   - Keeps current data
   - Removes baseline reference
   - Single confirmation

2. **Delete Current Data**
   - Keeps baseline
   - Removes current snapshot + history
   - Single confirmation

3. **Delete All Data (Danger Zone)**
   - Removes everything
   - Red danger zone section
   - Double confirmation required

**Visual Indicators:**
- ✅ Green cards when data exists
- ❌ Gray cards when no data
- 🗑️ Red delete buttons
- 💥 Red gradient "Delete All" button
- ⚠️ Warning emojis in confirmations

### 🔍 Debugging

**Backend Logs:**
```bash
# Real-time logs
tail -f /tmp/backend.log
```

**Frontend Console:**
- Open browser DevTools (F12 or Cmd+Option+I)
- Check Console tab for errors
- Check Network tab for API calls

**Database:**
- Backend connects to MongoDB Atlas
- Check connection in backend logs
- Verify collections in MongoDB dashboard

### ⚡ Quick Test Flow

1. **Upload Test Baseline:**
   - Go to http://localhost:5500/admin.html
   - Upload a CSV file as baseline
   - Check "Data Status" section

2. **View Leaderboard:**
   - Go to http://localhost:5500/
   - See players listed
   - Search by name or ID

3. **Test Delete:**
   - Return to admin panel
   - Click delete button
   - Confirm and watch it disappear

4. **Re-upload:**
   - Upload same or different file
   - Data refreshes automatically

### 🚨 Troubleshooting

**Port Already in Use:**
```bash
# Find what's using port 8000
lsof -ti:8000

# Kill it
kill -9 $(lsof -ti:8000)
```

**CORS Errors:**
- Check backend allows localhost:5500
- Check browser console for CORS messages
- Backend should allow localhost in CORS settings

**API Not Responding:**
```bash
# Check backend is running
curl http://localhost:8000/

# Restart backend
cd backend
uvicorn app.main:app --reload --port 8000
```

**Frontend Not Loading:**
```bash
# Check frontend server
curl http://localhost:5500/

# Restart frontend
cd frontend/public
python -m http.server 5500
```

### 📦 Files Modified for Local Dev

- `frontend/public/admin.js` - Auto-detect localhost
- `frontend/public/script.js` - Auto-detect localhost
- `frontend/public/player.js` - Auto-detect localhost
- `frontend/public/styles.css` - Delete button styles
- `backend/app/routes/upload.py` - Delete endpoints

### 🎯 Next Steps

1. **Test Delete Features:**
   - Try all three delete options
   - Verify confirmations work
   - Check data actually deletes

2. **Upload Test Data:**
   - Use sample CSV files in backend/
   - Test baseline + current workflow
   - Check leaderboard updates

3. **Review Changes:**
   - Check admin panel UI
   - Verify delete buttons appear
   - Test danger zone styling

4. **Deploy When Ready:**
   - Commit changes to git
   - Push to repository
   - Railway/Vercel auto-deploy

---

## 📋 Current Server Status

**Backend:** Running on http://localhost:8000 (PID: check with `ps aux | grep uvicorn`)
**Frontend:** Running on http://localhost:5500 (PID: check with `ps aux | grep http.server`)

**Ready to test! Open http://localhost:5500/admin.html to see the new delete features!**
