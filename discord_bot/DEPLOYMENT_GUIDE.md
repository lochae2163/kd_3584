# Discord Bot Deployment & Management Guide

## ✅ Deployment Checklist

Your bot is now deployed on Railway! Here's what to verify:

### 1. Check Bot Status

**In Railway Dashboard:**
- [ ] Service shows "Active" status
- [ ] Logs show: `✅ Logged in as Kingdom 3584 KvK Tracker`
- [ ] Logs show: `🚀 Bot is ready!`
- [ ] Logs show: `✅ Synced 5 command(s)`
- [ ] No error messages in logs

**In Discord:**
- [ ] Bot shows as "Online" (green circle)
- [ ] Bot appears in member list
- [ ] Typing `/` shows bot commands

### 2. Test Commands

Try each command in your Discord server:

```
/help
/stats YOUR_GOVERNOR_ID
/top kill_points_gained 10
/summary
/compare PLAYER1_ID PLAYER2_ID
```

Expected results:
- ✅ Commands appear in autocomplete
- ✅ Bot responds within 1-2 seconds
- ✅ Rich embeds display correctly
- ✅ Data matches web dashboard

---

## 🔧 Railway Configuration

### Environment Variables Required

Make sure these are set in Railway dashboard:

```
DISCORD_BOT_TOKEN=your_bot_token_here
API_URL=https://kd3584-production.up.railway.app
KVK_SEASON_ID=season_1
```

### Service Settings

- **Root Directory:** `discord_bot`
- **Start Command:** `python bot.py`
- **Builder:** Nixpacks
- **Region:** (Choose closest to you)

---

## 📊 Monitoring Your Bot

### Check Logs

**In Railway Dashboard:**
1. Click on your Discord bot service
2. Go to "Deployments" tab
3. Click on latest deployment
4. View "Logs" to see bot activity

**Common Log Messages:**

✅ **Normal Operation:**
```
✅ Logged in as Kingdom 3584 KvK Tracker
🚀 Bot is ready!
✅ Synced 5 command(s)
```

⚠️ **Warning (Non-critical):**
```
WARNING: Shard ID None heartbeat blocked for more than N seconds
```
This is normal Discord.py behavior, ignore it.

❌ **Errors to Fix:**
```
❌ DISCORD_BOT_TOKEN not set
```
→ Add token to Railway environment variables

```
Failed to fetch stats
```
→ Check API_URL is correct and backend is running

### Performance Metrics

**In Railway Dashboard → Metrics:**
- **CPU Usage:** Should be <5% most of the time
- **Memory Usage:** ~50-100 MB
- **Network:** Minimal (only when commands are used)

---

## 🚨 Troubleshooting

### Bot is Offline

**Check 1: Railway Service Status**
- Go to Railway dashboard
- Check if service is "Active"
- If crashed, check logs for error messages

**Check 2: Bot Token**
- Verify `DISCORD_BOT_TOKEN` is set correctly
- Token should start with a long string of characters
- No extra spaces or quotes

**Check 3: Redeploy**
```bash
# Push any change to trigger redeploy
git commit --allow-empty -m "Redeploy bot"
git push origin main
```

### Commands Not Appearing

**Solution 1: Wait for Sync**
- Commands can take 5-10 minutes to appear globally
- Try kicking and re-inviting bot

**Solution 2: Check Bot Permissions**
- Bot needs "Use Application Commands" permission
- Bot role should be above other roles

**Solution 3: Manual Sync**
- Bot automatically syncs on startup
- Check logs for "Synced X command(s)"

### Bot Responds but No Data

**Check API Connection:**
- Verify `API_URL` in Railway env vars
- Test API directly: `curl https://kd3584-production.up.railway.app/api/stats/summary`
- Check backend is running

**Check Season ID:**
- Verify `KVK_SEASON_ID` matches current season
- Try `/summary` to see if any data exists

### "Application did not respond" Error

**Cause:** Bot is slow or crashed

**Fix:**
1. Check Railway logs for errors
2. Restart service in Railway
3. Verify API is responding
4. Check network/connectivity

---

## 🔄 Updating the Bot

### Deploy New Version

When you update bot code:

```bash
# Make changes to discord_bot/bot.py
# Commit and push
git add discord_bot/
git commit -m "Update bot: describe your changes"
git push origin main
```

Railway will automatically:
- ✅ Detect changes
- ✅ Build new version
- ✅ Deploy automatically
- ✅ Restart bot

**Deployment time:** ~1-2 minutes

### Rollback to Previous Version

If new version has issues:

1. Go to Railway dashboard
2. Click on Discord bot service
3. Go to "Deployments" tab
4. Find previous working deployment
5. Click "Redeploy"

---

## 💰 Cost & Usage

### Railway Free Tier

- **500 hours/month** of runtime
- **Since bot runs 24/7:** 720 hours/month needed
- **Solution:** Upgrade to Hobby plan ($5/month) OR use multiple services

### Monitoring Usage

**In Railway Dashboard:**
- Check "Usage" tab
- Monitor hours consumed
- Set up billing alerts

### Staying on Free Tier

If you want to stay free:
1. Use Render.com for bot (100% free)
2. Keep backend on Railway
3. OR pause bot when not actively in KvK

---

## 🔐 Security

### Protect Your Token

- ✅ Never commit `.env` file to git
- ✅ Never share your bot token
- ✅ Store token only in Railway env vars
- ✅ Regenerate token if exposed

### Regenerate Token

If token is compromised:

1. Go to Discord Developer Portal
2. Go to your application
3. Go to "Bot" tab
4. Click "Reset Token"
5. Copy new token
6. Update Railway env var `DISCORD_BOT_TOKEN`
7. Redeploy service

---

## 📈 Usage Statistics

### Track Command Usage

Add to bot.py to log usage:

```python
@app_commands.command(name="stats")
async def stats(self, interaction: discord.Interaction, governor_id: str):
    logger.info(f"User {interaction.user} used /stats for {governor_id}")
    # ... rest of command
```

View in Railway logs to see:
- Most used commands
- Peak usage times
- Popular features

---

## 🎯 Quick Actions

### Restart Bot
1. Railway Dashboard → Your bot service
2. Click "Restart"
3. Wait ~30 seconds

### View Logs
1. Railway Dashboard → Your bot service
2. Click "Logs" tab
3. Use search/filter

### Change Season
1. Railway Dashboard → Variables
2. Update `KVK_SEASON_ID=season_2`
3. Bot restarts automatically

### Check Bot Status
- Discord: Look for green/gray dot
- Railway: Check service status
- Commands: Try `/help`

---

## 📞 Support

### Bot Not Working?

1. **Check Railway Logs First**
   - 90% of issues show in logs
   - Look for error messages

2. **Test API Separately**
   ```bash
   curl https://kd3584-production.up.railway.app/api/stats/summary
   ```

3. **Verify Environment Variables**
   - DISCORD_BOT_TOKEN set?
   - API_URL correct?
   - KVK_SEASON_ID valid?

4. **Try Restart**
   - Simple restart fixes most issues

### Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| Bot offline | Check Railway status, restart |
| No commands | Wait 10 min, re-invite bot |
| No data | Check API_URL, verify backend running |
| Slow responses | Check API performance, Railway metrics |
| "Not authenticated" | Backend may be down, check Railway |

---

## 🎉 Success Indicators

Your bot is working perfectly if:

✅ Green status in Discord
✅ All 5 commands work
✅ Responses under 2 seconds
✅ No errors in Railway logs
✅ Data matches web dashboard
✅ Embeds display correctly
✅ Alliance members can use it

---

## 📝 Maintenance Schedule

### Daily
- ✅ Check bot is online (quick Discord check)

### Weekly
- ✅ Review Railway logs for errors
- ✅ Check Railway usage/costs
- ✅ Test all commands

### Monthly
- ✅ Update dependencies if needed
- ✅ Review command usage stats
- ✅ Check for Discord.py updates

### After Each KvK Data Upload
- ✅ Test `/stats` with a few IDs
- ✅ Verify `/summary` shows new data
- ✅ Check `/top` rankings are current

---

## 🚀 Next Steps

Now that your bot is deployed:

1. **Announce to Alliance**
   ```
   🎉 NEW: KvK Stats Bot!

   Type / in Discord and use:
   /stats YOUR_ID - Check your stats
   /top - See leaderboard
   /summary - Kingdom stats

   Bot updates automatically when admin uploads new data!
   ```

2. **Create Bot Channel** (Optional)
   - Create #kvk-stats channel
   - Pin bot usage instructions
   - Members can check stats there

3. **Monitor Usage**
   - See which commands are popular
   - Gather feedback from alliance
   - Plan new features

4. **Enjoy!** 🎉
   - Your alliance now has instant stat access
   - No need to open website
   - Perfect for mobile users

---

**Your Discord bot is now running 24/7!** 🚀

Questions? Check Railway logs first, then the troubleshooting section above.
