# Discord Bot - Quick Command Reference

## 🎯 Most Used Commands

### Check Your Stats
```
/stats YOUR_GOVERNOR_ID
```
**Example:** `/stats 53242709`

**Returns:**
- Current Rank with medal emoji (🥇🥈🥉)
- Kill Points (total + gained)
- Power (total + gained)
- Deaths (total + gained)
- T5 Kills and T4 Kills
- KP/Death Ratio

---

### Top Players Leaderboard
```
/top [sort_by] [limit]
```

**Sort Options:**
- `kill_points_gained` ⚔️ (default)
- `deaths_gained` 💀
- `power` 💪
- `t5_kills` 🎖️
- `t4_kills` 🏅

**Examples:**
```
/top kill_points_gained 10
/top deaths_gained 5
/top power 25
/top t5_kills 15
```

**Limit:** 1-25 players (default: 10)

---

### Kingdom Summary
```
/summary
```

**Shows:**
- Total Kingdom Kill Points
- Total Kingdom Power
- Total Deaths
- Average stats per player
- Top 3 performers in each category
- Data collection period

---

### Compare Players
```
/compare PLAYER1_ID PLAYER2_ID
```

**Example:** `/compare 53242709 51540567`

**Shows:**
- Side-by-side stats comparison
- Difference calculations
- Visual indicators (🟢 winner, 🔴 lower)
- All key metrics

---

### Help Command
```
/help
```
Shows all commands with descriptions and examples.

---

## 📊 Understanding the Stats

### Kill Points (KP)
- **Total:** Your current total KP
- **Gained:** KP gained since baseline (snapshot taken at KvK start)
- Higher = More kills achieved

### Deaths
- **Total:** Your current total deaths
- **Gained:** Deaths since baseline
- Lower gained = Better performance

### Power
- **Total:** Your current total power
- **Gained:** Power increase since baseline
- Shows account growth during KvK

### T5/T4 Kills
- Number of Tier 5 and Tier 4 troops you've killed
- Higher tier kills = Stronger opponents defeated

### KP/Death Ratio
- Kill Points divided by Deaths
- Higher ratio = More efficient fighting
- Example: 5.2M KP / 100K deaths = 52.0 ratio

### Rank
- Your position in the leaderboard (1-500)
- Based on Kill Points Gained
- Updates when admin uploads new data

---

## 🏆 Leaderboard Medals

- 🥇 **Rank 1** - Gold Medal
- 🥈 **Rank 2** - Silver Medal
- 🥉 **Rank 3** - Bronze Medal
- 🎖️ **Rank 4-10** - Top 10
- No emoji for ranks 11+

---

## ⚙️ Technical Details

### Data Updates
- Data is manually uploaded by admin via web panel
- Bot shows data snapshot from specific time period
- Check `/summary` to see data collection timestamps

### Governor ID
- Find in Rise of Kingdoms: Tap Avatar → See ID number
- Usually 8 digits
- Same ID used in-game and in bot

### Response Time
- Bot typically responds in 1-3 seconds
- Depends on API server response time
- If slow, check API status at: https://kd3584-production.up.railway.app/

### Error Messages

**"Governor ID not found"**
- Player not in current KvK data
- Check if ID is correct
- Ensure admin has uploaded recent data

**"Application did not respond"**
- Bot may be restarting
- API server may be down
- Try again in 1-2 minutes

**"Invalid sort option"**
- Check spelling of sort parameter
- Use one of: kill_points_gained, deaths_gained, power, t5_kills, t4_kills

---

## 💡 Pro Tips

1. **Bookmark Your Stats**
   - Use the same `/stats YOUR_ID` command regularly
   - Track your progress over time

2. **Compare with Alliance Leaders**
   - Use `/compare YOUR_ID TOP_PLAYER_ID`
   - See where you can improve

3. **Set Personal Goals**
   - Check `/top` to see what top performers are achieving
   - Aim to improve your rank

4. **Monitor Efficiency**
   - Watch your KP/Death ratio
   - Higher ratio = Better fighting efficiency

5. **Stay Updated**
   - Use `/summary` to see when data was last updated
   - Coordinate with admin for regular updates

---

## 🔗 Useful Links

- **Admin Panel:** https://kd3584-production.up.railway.app/admin.html
- **API Status:** https://kd3584-production.up.railway.app/
- **Bot Source Code:** Check project repository
- **Support:** Contact server admins

---

## 🎮 Command Examples by Use Case

### Before KvK Fight
```
/stats YOUR_ID          # Check current baseline
/top kill_points_gained 10   # See who's leading
```

### After KvK Fight
```
/stats YOUR_ID          # See your gains
/compare YOUR_ID ENEMY_ID    # Compare with opponent
```

### Weekly Review
```
/summary                # Kingdom overview
/top power 25           # See overall rankings
/top deaths_gained 10   # Who's fighting hardest
```

### Alliance Strategy
```
/top t5_kills 10        # Who's taking down strong enemies
/top kill_points_gained 25   # Top performers
```

---

**Last Updated:** January 2, 2026
**Bot Version:** 1.0.0
**Data Source:** Kingdom 3584 KvK Tracker API
