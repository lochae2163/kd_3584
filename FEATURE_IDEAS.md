# Feature Ideas - Share Stats as Image

## What is "Share Stats as Image"?

This feature allows users to generate a beautiful image/card with their KvK stats that they can share on social media, Discord, or with alliance members.

### Example Use Cases:
1. **Discord Status** - Share your stats in alliance chat to show your progress
2. **Social Media** - Post your achievements on Twitter, Instagram, Facebook
3. **Alliance Recruitment** - Show your stats to prove your skill level
4. **Personal Records** - Save milestone images (e.g., "I hit 1B KP!")
5. **Bragging Rights** - Share when you reach rank 1 or top 10

---

## How It Would Work

### Option 1: Web Button (Easiest to Implement)

**Frontend (Website):**
1. User views their stats on the leaderboard
2. Clicks "Share as Image" button
3. Browser generates an image using Canvas API or html2canvas library
4. User can download or copy the image

**Example:**
```javascript
// Use html2canvas to convert DOM element to image
import html2canvas from 'html2canvas';

async function shareStatsAsImage(playerId) {
  const statsElement = document.getElementById(`player-${playerId}`);
  const canvas = await html2canvas(statsElement);
  const image = canvas.toDataURL('image/png');

  // Download or copy to clipboard
  downloadImage(image, 'my-kvk-stats.png');
}
```

**Visual Design:**
```
┌─────────────────────────────────────────┐
│  Kingdom 3584 KvK Tracker               │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │   🥇 Rank #12                       │ │
│  │   ⚔️ PlayerName (ID: 53242709)     │ │
│  ├────────────────────────────────────┤ │
│  │   Kill Points: 1.2B (+125M)        │ │
│  │   Power: 850M (+50M)               │ │
│  │   Deaths: 15M (+2M)                │ │
│  │   T5 Kills: 450M (+25M)            │ │
│  │   T4 Kills: 300M (+15M)            │ │
│  └────────────────────────────────────┘ │
│                                          │
│  Season 1 • Jan 3, 2026                 │
└─────────────────────────────────────────┘
```

---

### Option 2: Discord Bot Command (More Interactive)

**Discord Command:**
```
/share <governor_id>
```

**How it works:**
1. User types `/share 53242709` in Discord
2. Bot fetches player stats from API
3. Bot generates an image using Python PIL (Pillow) library
4. Bot uploads image to Discord as embed attachment
5. User can right-click → Save or share the image

**Python Implementation:**
```python
from PIL import Image, ImageDraw, ImageFont
import io

async def generate_stats_image(player_data):
    # Create blank image
    img = Image.new('RGB', (800, 600), color='#1a1a2e')
    draw = ImageDraw.Draw(img)

    # Load fonts
    font_title = ImageFont.truetype('arial.ttf', 32)
    font_stats = ImageFont.truetype('arial.ttf', 24)

    # Draw player name and rank
    draw.text((50, 50), f"🥇 Rank #{player_data['rank']}", fill='#FFD700', font=font_title)
    draw.text((50, 100), player_data['governor_name'], fill='#FFFFFF', font=font_title)

    # Draw stats...
    y_pos = 180
    for stat_name, stat_value in player_data['stats'].items():
        draw.text((50, y_pos), f"{stat_name}: {stat_value}", fill='#00D9FF', font=font_stats)
        y_pos += 50

    # Save to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return buffer

@app_commands.command(name="share", description="Generate shareable image of player stats")
async def share(self, interaction: discord.Interaction, governor_id: str):
    await interaction.response.defer()

    # Fetch player data
    player_data = await fetch_player_stats(governor_id)

    # Generate image
    image_buffer = await generate_stats_image(player_data)

    # Send as Discord file
    file = discord.File(image_buffer, filename=f'{governor_id}_stats.png')
    await interaction.followup.send(
        content="Here's your shareable stats card! 📊",
        file=file
    )
```

---

### Option 3: Backend API Endpoint (Most Flexible)

**API Endpoint:**
```
GET /api/player/{governor_id}/image?kvk_season_id=season_1
```

**How it works:**
1. User visits URL or clicks button on website
2. Backend generates image on-the-fly using Python PIL
3. Returns image as PNG response
4. Can be used in Discord, websites, or anywhere

**FastAPI Implementation:**
```python
from fastapi import Response
from PIL import Image, ImageDraw, ImageFont
import io

@app.get("/api/player/{governor_id}/image")
async def get_player_image(governor_id: str, kvk_season_id: str = "season_1"):
    # Fetch player data
    player = await get_player_stats(governor_id, kvk_season_id)

    # Generate image
    img = generate_stats_card(player)

    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    # Return as image response
    return Response(content=buffer.getvalue(), media_type="image/png")
```

**Then use in Discord or website:**
```html
<!-- Embed in website -->
<img src="https://kd3584-production.up.railway.app/api/player/53242709/image?kvk_season_id=season_1" />

<!-- Share in Discord -->
https://kd3584-production.up.railway.app/api/player/53242709/image?kvk_season_id=season_1
```

---

## Design Mockup

### Style 1: Minimalist Card
```
╔═══════════════════════════════════════╗
║  KINGDOM 3584 KvK TRACKER            ║
╠═══════════════════════════════════════╣
║                                       ║
║      🥇 RANK #12                      ║
║      ˢᵖtomiCH                         ║
║      ID: 53242709                     ║
║                                       ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                       ║
║  ⚔️  Kill Points:  1.2B  (+125M)     ║
║  💪 Power:        850M  (+50M)       ║
║  ☠️  Deaths:       15M  (+2M)        ║
║  🎯 T5 Kills:     450M  (+25M)       ║
║  ⚡ T4 Kills:     300M  (+15M)       ║
║                                       ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                       ║
║  Season 1 • January 3, 2026          ║
║                                       ║
╚═══════════════════════════════════════╝
```

### Style 2: Gaming Style (Dark Theme)
```
Background: Dark gradient (#1a1a2e to #16213e)
┌───────────────────────────────────────┐
│                                       │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃  🏆 RANK #12 🏆                 ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                                       │
│       ˢᵖtomiCH                        │
│       Governor ID: 53242709           │
│                                       │
│  ╔══════════════════════════════╗    │
│  ║  KILL POINTS                  ║    │
│  ║  1,200,000,000                ║    │
│  ║  🟢 +125,000,000              ║    │
│  ╚══════════════════════════════╝    │
│                                       │
│  ╔══════════════════════════════╗    │
│  ║  POWER                        ║    │
│  ║  850,000,000                  ║    │
│  ║  🟢 +50,000,000               ║    │
│  ╚══════════════════════════════╝    │
│                                       │
│  Deaths: 15M (+2M)  T5: 450M (+25M)  │
│  T4 Kills: 300M (+15M)                │
│                                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  KD 3584 • Season 1 • Jan 3, 2026    │
└───────────────────────────────────────┘
```

### Style 3: Player Card (Like Trading Card)
```
┌───────────────────────────────────────┐
│  ┌─────────────────────────────────┐ │
│  │     [Player Avatar/Icon]         │ │
│  │                                  │ │
│  │       ˢᵖtomiCH                   │ │
│  │    🥇 Rank #12 🥇               │ │
│  └─────────────────────────────────┘ │
│                                       │
│  ┌──────────────┬──────────────────┐ │
│  │ Kill Points  │  1.2B (+125M)    │ │
│  ├──────────────┼──────────────────┤ │
│  │ Power        │  850M (+50M)     │ │
│  ├──────────────┼──────────────────┤ │
│  │ Deaths       │  15M (+2M)       │ │
│  ├──────────────┼──────────────────┤ │
│  │ T5 Kills     │  450M (+25M)     │ │
│  ├──────────────┼──────────────────┤ │
│  │ T4 Kills     │  300M (+15M)     │ │
│  └──────────────┴──────────────────┘ │
│                                       │
│  Kingdom 3584 • Season 1             │
│  kd-3584.vercel.app                  │
└───────────────────────────────────────┘
```

---

## Implementation Steps

### Phase 1: Basic Implementation (1-2 days)
1. **Choose approach** (Discord bot vs web vs API)
2. **Set up PIL/Pillow** for image generation
3. **Create basic card design** (Style 1 - minimalist)
4. **Test with sample data**

### Phase 2: Enhanced Design (2-3 days)
1. **Add custom fonts** (download gaming/military style fonts)
2. **Add background images** or gradients
3. **Add rank medals** (🥇🥈🥉 as actual images)
4. **Color coding** for positive/negative deltas

### Phase 3: Customization (3-4 days)
1. **Multiple themes** (dark, light, gaming, minimal)
2. **User preferences** (choose colors, style)
3. **Custom backgrounds** (upload your own)
4. **Watermark/branding** (Kingdom logo)

### Phase 4: Advanced Features (5-7 days)
1. **Animated GIFs** (show progress over time)
2. **Comparison images** (2 players side-by-side)
3. **Leaderboard image** (top 10 in one image)
4. **QR code** to player profile page

---

## Required Libraries

### Python (Backend/Discord Bot):
```bash
pip install Pillow  # Image generation
pip install qrcode  # QR codes (optional)
```

### JavaScript (Frontend):
```bash
npm install html2canvas  # DOM to image
npm install canvas      # Node canvas API
npm install sharp       # Image processing
```

---

## Example Code - Discord Bot Share Command

```python
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import discord
from discord import app_commands

@app_commands.command(name="share", description="Generate shareable stats image")
@app_commands.describe(governor_id="Your Governor ID")
async def share(self, interaction: discord.Interaction, governor_id: str):
    await interaction.response.defer()

    try:
        # Fetch player data from API
        url = f"{API_URL}/api/player/{governor_id}?kvk_season_id={KVK_SEASON_ID}"
        async with self.session.get(url) as response:
            if response.status != 200:
                await interaction.followup.send("❌ Player not found", ephemeral=True)
                return

            data = await response.json()
            player = data.get('player', data)

        # Generate image
        img = await self.generate_stats_card(player)

        # Save to buffer
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        # Send to Discord
        file = discord.File(buffer, filename=f'stats_{governor_id}.png')
        embed = discord.Embed(
            title="📊 Stats Card Generated!",
            description=f"Here's the shareable stats card for **{player['governor_name']}**",
            color=discord.Color.blue()
        )
        embed.set_image(url=f"attachment://stats_{governor_id}.png")

        await interaction.followup.send(embed=embed, file=file)

    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

async def generate_stats_card(self, player):
    """Generate beautiful stats card"""
    # Image dimensions
    WIDTH, HEIGHT = 800, 600

    # Create image with dark background
    img = Image.new('RGB', (WIDTH, HEIGHT), color='#1a1a2e')
    draw = ImageDraw.Draw(img)

    # Try to load custom font, fallback to default
    try:
        font_title = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 40)
        font_subtitle = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 28)
        font_stats = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
        font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
    except:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_stats = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw header
    draw.text((WIDTH//2, 40), "KINGDOM 3584 KvK TRACKER", fill='#00D9FF', font=font_small, anchor='mt')

    # Draw rank
    rank = player.get('rank', 'N/A')
    rank_emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "🏆"
    draw.text((WIDTH//2, 100), f"{rank_emoji} RANK #{rank} {rank_emoji}", fill='#FFD700', font=font_title, anchor='mt')

    # Draw player name
    draw.text((WIDTH//2, 160), player['governor_name'], fill='#FFFFFF', font=font_subtitle, anchor='mt')
    draw.text((WIDTH//2, 200), f"ID: {player['governor_id']}", fill='#888888', font=font_small, anchor='mt')

    # Draw separator line
    draw.line([(50, 240), (WIDTH-50, 240)], fill='#444444', width=2)

    # Draw stats
    stats = player.get('stats', {})
    delta = player.get('delta', {})

    y_pos = 280
    stat_configs = [
        ('⚔️ Kill Points:', 'kill_points'),
        ('💪 Power:', 'power'),
        ('☠️ Deaths:', 'deads'),
        ('🎯 T5 Kills:', 't5_kills'),
        ('⚡ T4 Kills:', 't4_kills'),
    ]

    for emoji_label, field in stat_configs:
        stat_value = self.format_number(stats.get(field, 0))
        delta_value = delta.get(field, 0)
        delta_color = '#00FF00' if delta_value > 0 else '#FF0000' if delta_value < 0 else '#888888'
        delta_text = f"(+{self.format_number(delta_value)})" if delta_value > 0 else f"({self.format_number(delta_value)})" if delta_value < 0 else "(+0)"

        draw.text((70, y_pos), emoji_label, fill='#FFFFFF', font=font_stats, anchor='lt')
        draw.text((300, y_pos), stat_value, fill='#00D9FF', font=font_stats, anchor='lt')
        draw.text((550, y_pos), delta_text, fill=delta_color, font=font_stats, anchor='lt')

        y_pos += 45

    # Draw footer
    draw.line([(50, HEIGHT-80), (WIDTH-50, HEIGHT-80)], fill='#444444', width=2)
    draw.text((WIDTH//2, HEIGHT-50), f"Season 1 • {datetime.now().strftime('%B %d, %Y')}", fill='#888888', font=font_small, anchor='mt')
    draw.text((WIDTH//2, HEIGHT-25), "kd-3584.vercel.app", fill='#00D9FF', font=font_small, anchor='mt')

    return img
```

---

## Recommendation

**Start with Discord Bot `/share` command** because:
1. ✅ Easy to implement (1-2 days)
2. ✅ High user engagement (people love sharing in Discord)
3. ✅ Uses existing API infrastructure
4. ✅ No frontend changes needed
5. ✅ Can add web version later

**Next Step:** Want me to implement this feature?
