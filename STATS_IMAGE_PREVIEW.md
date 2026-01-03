# Stats Image Card - Visual Preview

## What It Looks Like

When users type `/stats <governor_id>`, they'll receive a beautiful PNG image instead of a text embed.

### Image Dimensions
- **Size:** 900px × 700px
- **Format:** PNG
- **File size:** ~50-100 KB

### Layout

```
╔═══════════════════════════════════════════════════════════════╗
║                KINGDOM 3584 KVK TRACKER                       ║
║                    (Dark blue header bar)                     ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║                   🥇  RANK #12  🥇                            ║
║                  (Large gold text)                            ║
║                                                               ║
║                      ˢᵖtomiCH                                 ║
║                  (White, large font)                          ║
║                                                               ║
║                  ID: 53242709                                 ║
║                  (Gray, small font)                           ║
║                                                               ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                               ║
║  ⚔️  Kill Points        1.2B              (+125M)            ║
║                      (Cyan blue)         (Green)             ║
║                                                               ║
║  💪 Power              850M               (+50M)             ║
║                      (Cyan blue)         (Green)             ║
║                                                               ║
║  ☠️  Deaths             15M                (+2M)             ║
║                      (Cyan blue)          (Red)              ║
║                                                               ║
║  🎯 T5 Kills           450M               (+25M)             ║
║                      (Cyan blue)         (Green)             ║
║                                                               ║
║  ⚡ T4 Kills           300M               (+15M)             ║
║                      (Cyan blue)         (Green)             ║
║                                                               ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                               ║
║              Season 1 • January 4, 2026                       ║
║                  kd-3584.vercel.app                           ║
║                     (Gray footer)                             ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

## Color Scheme

### Background
- **Gradient:** Dark blue (#0f1419) to slightly lighter blue (#1a212e)
- Creates professional depth and modern look

### Text Colors
- **Header:** Cyan (#00d9ff) - "KINGDOM 3584 KVK TRACKER"
- **Rank:** Gold (#ffd700) - Rank number and medals
- **Player Name:** White (#ffffff) - High contrast
- **Player ID:** Gray (#888888) - Subtle
- **Stat Labels:** Light Gray (#aaaaaa) - "Kill Points", "Power", etc.
- **Stat Values:** Cyan (#00d9ff) - Main numbers
- **Delta Positive:** Bright Green (#00ff88) - Gains
- **Delta Negative:** Red (#ff4444) - Losses
- **Delta Zero:** Gray (#888888) - No change
- **Footer:** Gray (#888888) - Date and website

### Lines & Borders
- **Separator Lines:** Dark Gray (#444444)
- **Header Bar:** Dark Blue (#1a1f2e)

## Rank Display Variations

### Rank 1 (Gold Medal)
```
🥇  RANK #1  🥇
```

### Rank 2 (Silver Medal)
```
🥈  RANK #2  🥈
```

### Rank 3 (Bronze Medal)
```
🥉  RANK #3  🥉
```

### Rank 4+ (Trophy)
```
🏆  RANK #12  🏆
```

## Delta Display Examples

### Positive Gain (Green)
```
Kill Points:  1.2B    (+125M)
                      ↑ Green
```

### Negative Loss (Red)
```
Deaths:  15M    (+2M)
                 ↑ Red (more deaths)
```

### No Change (Gray)
```
Power:  850M    (+0)
                ↑ Gray
```

## Font Hierarchy

### DejaVu Fonts (used on Railway)
1. **Header:** DejaVuSans-Bold, 24pt
2. **Rank:** DejaVuSans-Bold, 48pt (largest)
3. **Player Name:** DejaVuSans, 32pt
4. **Stats Values:** DejaVuSans, 28pt
5. **Stat Labels:** DejaVuSans, 24pt
6. **Small Text:** DejaVuSans, 20pt (ID, footer)

### Fallback
- If fonts fail to load, uses PIL default font (still readable)

## User Experience

### Discord Display
1. User types: `/stats 53242709`
2. Bot responds: "📊 **Stats for ˢᵖtomiCH** (Right-click to save image)"
3. Image appears inline in chat
4. Click to view full size
5. Right-click → Save Image As... to download

### What Users Can Do
- ✅ View stats immediately in Discord
- ✅ Right-click to save as PNG
- ✅ Share in other Discord channels
- ✅ Post on Twitter, Instagram, Facebook
- ✅ Send to friends via DM
- ✅ Save as personal record/milestone
- ✅ Use for alliance recruitment

## Technical Details

### Image Generation Process
1. Create 900x700 canvas with dark background
2. Draw gradient effect line-by-line
3. Render header bar with title
4. Draw rank with medals
5. Draw player name and ID
6. Draw separator line
7. Loop through 5 stats, rendering each with:
   - Emoji + label (left)
   - Stat value (center-right, cyan)
   - Delta value (right, color-coded)
8. Draw bottom separator
9. Render footer with date and website
10. Save to BytesIO buffer as PNG
11. Send to Discord as file attachment

### Performance
- **Generation time:** ~100-300ms per image
- **Memory usage:** ~1-2 MB per request
- **Railway compatible:** Uses system fonts, no custom font files needed

### Error Handling
- If fonts fail → Uses default PIL fonts
- If image generation fails → Sends error message
- Logs errors for debugging

## Examples of Use

### Example 1: Check Personal Stats
```
User: /stats 53242709
Bot: [Sends beautiful PNG image]
User: Saves image to phone
```

### Example 2: Share Achievement
```
User: /stats 53242709
Bot: [Sends image showing Rank #1]
User: Right-clicks → Copy Image
User: Pastes in #announcements channel
Message: "Just hit Rank 1! 🎉"
```

### Example 3: Compare with Friend
```
User: /stats 53242709    (their stats)
User: /stats 51540567    (friend's stats)
Both images appear in chat for easy visual comparison
```

### Example 4: Recruitment
```
Recruiter: Posts stats image in recruitment Discord
Message: "Looking for alliance! Here are my stats:"
Other alliances see impressive numbers and send offers
```

### Example 5: Social Media
```
User: /stats 53242709
User: Downloads image
User: Posts to Twitter with caption:
"Just reached 1 Billion Kill Points in RoK! 💪🔥 #RiseofKingdoms"
```

## Future Enhancements (Optional)

### Could Add Later:
1. **Custom backgrounds** - Let users choose themes
2. **Alliance logo** - Watermark with alliance emblem
3. **QR code** - Scan to view full profile
4. **Animated version** - GIF showing stats growth over time
5. **Comparison mode** - Two players side-by-side
6. **Top 10 version** - Leaderboard in image form
7. **Custom colors** - User preferences
8. **Dark/Light mode** - Theme toggle

### Advanced Ideas:
1. **Video generation** - MP4 with animated stats
2. **3D effects** - Shadows and depth
3. **Seasonal themes** - Different styles per KvK
4. **Achievement badges** - Show milestones reached
5. **Sparkles/effects** - For new records

---

## Testing

### On Railway
Once deployed, test with:
```
/stats 53242709
```

Should receive PNG image in 1-2 seconds.

### Check Railway Logs
Look for:
```
✅ Logged in as Kingdom 3584 KvK Tracker
✅ Synced 5 command(s) to guild: [Your Server]
```

### Troubleshooting
If fonts don't load:
- Check `/usr/share/fonts/truetype/dejavu/` exists on Railway
- Falls back to default fonts (still works)

If image generation fails:
- Check Railway logs for PIL errors
- Verify Pillow installed correctly
- Check memory limits (unlikely issue)

---

**Status:** ✅ Deployed and Ready
**Version:** 1.1.0
**Feature:** Stats as Image (Auto-shareable)
