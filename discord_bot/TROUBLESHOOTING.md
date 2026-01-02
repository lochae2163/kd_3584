# Discord Bot Troubleshooting Guide

## Error: "The application did not respond"

This error means the Discord bot is **not running** or **crashed**. Here's how to fix it:

---

## ✅ Step 1: Check Railway Bot Service

1. Go to **Railway Dashboard**: https://railway.app/dashboard
2. Find your **Discord Bot service** (separate from your backend API)
3. Check the status indicator:
   - 🟢 **Green** = Bot is running
   - 🔴 **Red** = Bot is crashed/stopped
   - 🟡 **Yellow** = Bot is deploying

---

## ✅ Step 2: Check Railway Logs

1. Click on your Discord Bot service
2. Click **"Deployments"** tab
3. Click the latest deployment
4. Click **"View Logs"**

### What to Look For:

**✅ GOOD - Bot is working:**
```
✅ Logged in as Kingdom 3584 KvK Tracker#1234
📊 Connected to 1 guilds
🚀 Bot is ready!
✅ Synced 5 command(s)
```

**❌ BAD - Bot crashed:**
```
❌ DISCORD_BOT_TOKEN not set in environment variables!
ERROR: discord.errors.LoginFailure
Traceback (most recent call last):
```

---

## ✅ Step 3: Verify Environment Variables

Your Discord bot needs these environment variables set in Railway:

### Required Variables:

1. **DISCORD_BOT_TOKEN**
   - Your Discord bot token from Discord Developer Portal
   - Get it from: https://discord.com/developers/applications
   - Click your app → Bot → Reset Token → Copy

2. **API_URL** (optional)
   - Default: `https://kd3584-production.up.railway.app`
   - Your backend API URL

3. **KVK_SEASON_ID** (optional)
   - Default: `season_1`
   - Current KvK season to track

### How to Set Variables in Railway:

1. Go to your Discord Bot service
2. Click **"Variables"** tab
3. Click **"+ New Variable"**
4. Add each variable:
   ```
   DISCORD_BOT_TOKEN = your_bot_token_here
   API_URL = https://kd3584-production.up.railway.app
   KVK_SEASON_ID = season_1
   ```
5. Click **"Deploy"** to restart with new variables

---

## ✅ Step 4: Check Discord Bot Status in Discord

1. Open your Discord server
2. Look at the bot in the member list (right sidebar)
3. Check the status indicator:
   - 🟢 **Green** = Bot is online
   - ⚫ **Gray** = Bot is offline

If bot shows **gray/offline**, the Railway service is not running.

---

## ✅ Step 5: Verify Bot Deployment Files

Make sure these files exist in your `discord_bot/` folder:

- ✅ `bot.py` - Main bot code
- ✅ `requirements.txt` - Python dependencies
- ✅ `railway.json` - Railway configuration
- ✅ `runtime.txt` - Python version
- ✅ `.env.example` - Environment variable template (not used in production)

---

## ✅ Step 6: Manual Redeploy

If bot is still not working:

1. In Railway, click your Discord Bot service
2. Click **"Settings"** tab
3. Scroll down to **"Service"**
4. Click **"Redeploy"**
5. Wait 2-3 minutes for deployment
6. Check logs again

---

## 🔧 Common Issues and Fixes

### Issue 1: "DISCORD_BOT_TOKEN not set"

**Solution:**
- Add `DISCORD_BOT_TOKEN` to Railway environment variables
- Make sure you copied the full token (no extra spaces)
- Token should start with something like `MTIzNDU2...`

### Issue 2: "discord.errors.LoginFailure: Improper token has been passed"

**Solution:**
- Your bot token is invalid or expired
- Go to Discord Developer Portal
- Reset your bot token and get a new one
- Update the token in Railway variables
- Redeploy

### Issue 3: Bot shows online but commands don't work

**Solution:**
- Commands may not be synced yet (takes 1-60 minutes)
- Make sure bot has "Use Application Commands" permission
- Try re-inviting bot with correct OAuth2 URL:
  1. Go to Discord Developer Portal
  2. OAuth2 → URL Generator
  3. Select: `bot` + `applications.commands`
  4. Select permissions: Send Messages, Embed Links, Use Slash Commands
  5. Copy URL and invite bot again

### Issue 4: "API is offline" or timeout errors

**Solution:**
- Check your backend API is running
- Verify `API_URL` in Railway variables is correct
- Test API: https://kd3584-production.up.railway.app/
- Should return status 200 or 405

### Issue 5: Railway shows "Build Failed"

**Solution:**
- Check `requirements.txt` has correct dependencies:
  ```
  discord.py==2.3.2
  aiohttp==3.9.1
  python-dotenv==1.0.0
  requests==2.31.0
  ```
- Check `runtime.txt` specifies Python version:
  ```
  python-3.11.7
  ```
- Check build logs for specific error

### Issue 6: Bot keeps restarting/crashing

**Solution:**
- Check logs for error messages
- Common causes:
  - Missing environment variables
  - Invalid bot token
  - API URL is wrong
  - Network connectivity issues
- Railway has auto-restart on failure (max 10 retries)

---

## 🚀 Quick Fix Checklist

Run through this checklist:

- [ ] Railway bot service shows **green** (running)
- [ ] Environment variable `DISCORD_BOT_TOKEN` is set
- [ ] Bot token is valid and not expired
- [ ] Bot shows **online** (green) in Discord
- [ ] Logs show "Bot is ready! ✅ Synced 5 command(s)"
- [ ] Backend API is online: https://kd3584-production.up.railway.app/
- [ ] Bot has correct permissions in Discord server
- [ ] Waited 5+ minutes after deployment for commands to sync

---

## 📞 Still Not Working?

If you've tried everything above and it's still not working:

### Check These:

1. **Railway Free Tier Limits**
   - Free tier has 500 hours/month
   - Check if you've exceeded limits
   - Upgrade to Hobby plan ($5/month) if needed

2. **Discord Bot Intents**
   - Go to Discord Developer Portal
   - Bot tab → Enable "Message Content Intent"
   - Save changes

3. **Multiple Deployments**
   - Make sure you don't have multiple bot instances running
   - Only one Railway service for Discord bot
   - Check if bot is also running locally on your computer

4. **Discord API Status**
   - Check: https://discordstatus.com/
   - Discord may be having issues

---

## 🔍 Debug Commands

Run these locally to debug:

```bash
# Check API is accessible
curl https://kd3584-production.up.railway.app/

# Test bot can reach API
cd discord_bot
python3 check_bot_status.py

# Test bot locally (requires .env file with DISCORD_BOT_TOKEN)
cd discord_bot
python3 bot.py
```

If bot works locally but not on Railway, the issue is with Railway configuration.

---

## 📋 What to Send for Help

If asking for help, provide:

1. **Railway deployment logs** (last 50 lines)
2. **Discord bot status** (online/offline)
3. **Environment variables set** (don't share the actual token!)
4. **Error messages** from Discord
5. **Output from `check_bot_status.py`**

---

**Last Updated:** January 2, 2026
**Bot Version:** 1.0.0
