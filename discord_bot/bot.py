import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp
import os
from datetime import datetime
from typing import Optional
import logging
from PIL import Image, ImageDraw, ImageFont
import io

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_URL = os.getenv('API_URL', 'https://kd3584-production.up.railway.app')
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Global variable for active season (will be fetched on startup)
ACTIVE_SEASON_ID = None

if not DISCORD_TOKEN:
    logger.error("❌ DISCORD_BOT_TOKEN not set in environment variables!")
    exit(1)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


class KvKBot(commands.Cog):
    """Kingdom 3584 KvK Tracker Bot"""

    def __init__(self, bot):
        self.bot = bot
        self.session = None

    async def cog_load(self):
        """Initialize aiohttp session"""
        # Set timeout to 10 seconds for API requests
        timeout = aiohttp.ClientTimeout(total=10)
        self.session = aiohttp.ClientSession(timeout=timeout)

        # Fetch active season on startup
        await self.fetch_active_season()

    async def cog_unload(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()

    async def fetch_active_season(self):
        """Fetch and cache the active season ID"""
        global ACTIVE_SEASON_ID
        try:
            url = f"{API_URL}/api/seasons/active"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    ACTIVE_SEASON_ID = data.get('season_id', 'season_6')
                    logger.info(f"✅ Active season set to: {ACTIVE_SEASON_ID}")
                else:
                    # Fallback to season_6 if API fails
                    ACTIVE_SEASON_ID = 'season_6'
                    logger.warning(f"⚠️ Failed to fetch active season, using fallback: {ACTIVE_SEASON_ID}")
        except Exception as e:
            ACTIVE_SEASON_ID = 'season_6'
            logger.error(f"❌ Error fetching active season: {e}, using fallback: {ACTIVE_SEASON_ID}")

    def get_season_id(self):
        """Get the current active season ID"""
        return ACTIVE_SEASON_ID or 'season_6'

    def format_number(self, num):
        """Format number: abbreviated (B/M) for millions+, full with commas for under 1M"""
        if num is None or num == 0:
            return "0"

        num = int(num)

        # For 1 million and above, use abbreviated format
        if abs(num) >= 1_000_000_000:
            return f"{num / 1_000_000_000:.1f}B"
        elif abs(num) >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        else:
            # For under 1 million, show full number with commas
            return f"{num:,}"

    def format_delta(self, value):
        """Format delta value with color indicators

        Args:
            value: The delta value to format

        Returns:
            Green circle for positive (+), red circle for negative (-)
        """
        if value == 0:
            return f"(+0)"
        elif value > 0:
            # Positive change = green
            return f"🟢 (+{self.format_number(value)})"
        else:
            # Negative change = red (keep the minus sign)
            return f"🔴 (-{self.format_number(abs(value))})"

    async def generate_stats_image(self, player_data):
        """Generate beautiful stats card image"""
        # Image dimensions
        WIDTH, HEIGHT = 900, 700

        # Create image with dark gradient background
        img = Image.new('RGB', (WIDTH, HEIGHT), color='#0f1419')
        draw = ImageDraw.Draw(img)

        # Draw gradient background effect
        for y in range(HEIGHT):
            r = int(15 + (26 - 15) * y / HEIGHT)
            g = int(20 + (33 - 20) * y / HEIGHT)
            b = int(25 + (46 - 25) * y / HEIGHT)
            draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

        # Try to load fonts, fallback to default
        try:
            # Use DejaVu fonts (available on most Linux systems including Railway)
            font_header = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
            font_title = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 48)
            font_subtitle = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 32)
            font_stats = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 28)
            font_label = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
            font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
        except:
            # Fallback to default font
            font_header = ImageFont.load_default()
            font_title = ImageFont.load_default()
            font_subtitle = ImageFont.load_default()
            font_stats = ImageFont.load_default()
            font_label = ImageFont.load_default()
            font_small = ImageFont.load_default()

        stats = player_data.get('stats', {})
        delta = player_data.get('delta', {})
        rank = player_data.get('rank', 'N/A')

        # Draw header bar
        draw.rectangle([(0, 0), (WIDTH, 80)], fill='#1a1f2e')
        draw.text((WIDTH//2, 40), "KINGDOM 3584 KvK TRACKER", fill='#00d9ff', font=font_header, anchor='mm')

        # Draw rank badge
        rank_emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "🏆"
        rank_text = f"RANK #{rank}"
        draw.text((WIDTH//2, 130), f"{rank_emoji}  {rank_text}  {rank_emoji}", fill='#ffd700', font=font_title, anchor='mm')

        # Draw player name
        draw.text((WIDTH//2, 195), player_data['governor_name'], fill='#ffffff', font=font_subtitle, anchor='mm')
        draw.text((WIDTH//2, 235), f"ID: {player_data['governor_id']}", fill='#888888', font=font_small, anchor='mm')

        # Draw separator line
        draw.line([(60, 270), (WIDTH-60, 270)], fill='#444444', width=3)

        # Draw stats section
        y_pos = 320
        stat_configs = [
            ('⚔️  Kill Points', 'kill_points'),
            ('💪 Power', 'power'),
            ('☠️  Deaths', 'deads'),
            ('🎯 T5 Kills', 't5_kills'),
            ('⚡ T4 Kills', 't4_kills'),
        ]

        for emoji_label, field in stat_configs:
            stat_value = stats.get(field, 0)
            delta_value = delta.get(field, 0)

            # Determine delta color
            if delta_value > 0:
                delta_color = '#00ff88'  # Green
                delta_prefix = '+'
            elif delta_value < 0:
                delta_color = '#ff4444'  # Red
                delta_prefix = ''
            else:
                delta_color = '#888888'  # Gray
                delta_prefix = ''

            # Format numbers
            stat_formatted = self.format_number(stat_value)
            delta_formatted = self.format_number(abs(delta_value))

            # Draw label
            draw.text((80, y_pos), emoji_label, fill='#aaaaaa', font=font_label, anchor='lm')

            # Draw stat value (right-aligned)
            draw.text((WIDTH - 320, y_pos), stat_formatted, fill='#00d9ff', font=font_stats, anchor='rm')

            # Draw delta (in parentheses)
            delta_text = f"({delta_prefix}{delta_formatted})"
            draw.text((WIDTH - 80, y_pos), delta_text, fill=delta_color, font=font_label, anchor='rm')

            y_pos += 65

        # Draw bottom separator
        draw.line([(60, HEIGHT-100), (WIDTH-60, HEIGHT-100)], fill='#444444', width=3)

        # Draw footer
        footer_text = f"Season 1 • {datetime.now().strftime('%B %d, %Y')}"
        draw.text((WIDTH//2, HEIGHT-60), footer_text, fill='#888888', font=font_small, anchor='mm')
        draw.text((WIDTH//2, HEIGHT-30), "kd-3584.vercel.app", fill='#00d9ff', font=font_small, anchor='mm')

        return img

    def create_player_embed(self, player_data):
        """Create rich embed for player stats"""
        stats = player_data.get('stats', {})
        delta = player_data.get('delta', {})
        rank = player_data.get('rank', 'N/A')

        # Determine rank emoji
        if rank == 1:
            rank_display = "🥇 #1"
        elif rank == 2:
            rank_display = "🥈 #2"
        elif rank == 3:
            rank_display = "🥉 #3"
        else:
            rank_display = f"#{rank}"

        embed = discord.Embed(
            title=f"📊 {player_data['governor_name']}",
            description=f"**Rank:** {rank_display} • **Governor ID:** {player_data['governor_id']}\n━━━━━━━━━━━━━━━━━━━━━━━━",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )

        # Format stats with deltas in brackets
        kp_total = self.format_number(stats.get('kill_points', 0))
        kp_delta = self.format_delta(delta.get('kill_points', 0))

        power_total = self.format_number(stats.get('power', 0))
        power_delta = self.format_delta(delta.get('power', 0))

        deaths_total = self.format_number(stats.get('deads', 0))
        deaths_delta = self.format_delta(delta.get('deads', 0))

        t5_total = self.format_number(stats.get('t5_kills', 0))
        t5_delta = self.format_delta(delta.get('t5_kills', 0))

        t4_total = self.format_number(stats.get('t4_kills', 0))
        t4_delta = self.format_delta(delta.get('t4_kills', 0))

        embed.add_field(
            name="⚔️ **Kill Points**",
            value=f"`{kp_total}` {kp_delta}\n\u200b",
            inline=False
        )

        embed.add_field(
            name="💪 **Power**",
            value=f"`{power_total}` {power_delta}\n\u200b",
            inline=False
        )

        embed.add_field(
            name="☠️ **Deaths**",
            value=f"`{deaths_total}` {deaths_delta}\n\u200b",
            inline=False
        )

        embed.add_field(
            name="🎯 **T5 Kills**",
            value=f"`{t5_total}` {t5_delta}\n\u200b",
            inline=False
        )

        embed.add_field(
            name="⚡ **T4 Kills**",
            value=f"`{t4_total}` {t4_delta}\n\u200b",
            inline=False
        )

        embed.set_footer(text="Kingdom 3584 KvK Tracker")

        return embed

    async def player_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for player search - search by name or ID"""
        try:
            # Fetch all players from leaderboard (API max limit is 500)
            url = f"{API_URL}/api/leaderboard?kvk_season_id={self.get_season_id()}&limit=500"

            logger.info(f"Autocomplete triggered with input: '{current}'")

            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"API returned status {response.status}")
                    return []

                data = await response.json()
                players = data.get('leaderboard', [])
                logger.info(f"Fetched {len(players)} players from API")

            # If no input, return top 25 by rank
            if not current or current.strip() == "":
                choices = [
                    app_commands.Choice(
                        name=f"#{p['rank']} {p['governor_name']} (ID: {p['governor_id']})",
                        value=p['governor_id']
                    )
                    for p in players[:25]
                ]
                logger.info(f"Returning {len(choices)} default choices")
                return choices

            # Search by name or ID
            current_lower = current.lower().strip()
            matches = []

            for player in players:
                name = player['governor_name'].lower()
                gov_id = str(player['governor_id'])

                # Match by name or ID
                if current_lower in name or current.strip() in gov_id:
                    matches.append(player)

                # Limit to 25 results (Discord autocomplete limit)
                if len(matches) >= 25:
                    break

            logger.info(f"Found {len(matches)} matches for '{current}'")

            choices = [
                app_commands.Choice(
                    name=f"#{p['rank']} {p['governor_name']} (ID: {p['governor_id']})",
                    value=str(p['governor_id'])
                )
                for p in matches
            ]

            return choices

        except Exception as e:
            logger.error(f"Autocomplete error: {e}", exc_info=True)
            return []

    @app_commands.command(name="stats", description="Get your KvK stats by Governor ID or Name")
    @app_commands.describe(player="Search by player name or Governor ID")
    @app_commands.autocomplete(player=player_autocomplete)
    async def stats(self, interaction: discord.Interaction, player: str):
        """Get player stats by Governor ID or Name"""
        await interaction.response.defer()

        try:
            # First, try as governor_id
            url = f"{API_URL}/api/player/{player}?kvk_season_id={self.get_season_id()}"

            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    player_data = data.get('player', data)
                    embed = self.create_player_embed(player_data)
                    await interaction.followup.send(embed=embed)
                    return

            # If not found by ID, try searching by name
            logger.info(f"Player '{player}' not found by ID, searching by name...")
            url = f"{API_URL}/api/leaderboard?kvk_season_id={self.get_season_id()}&limit=500"

            async with self.session.get(url) as response:
                if response.status != 200:
                    await interaction.followup.send(
                        "❌ Failed to fetch stats. Please try again later.",
                        ephemeral=True
                    )
                    return

                data = await response.json()
                players = data.get('leaderboard', [])

                # Search for player by name (case-insensitive)
                player_lower = player.lower().strip()
                matches = [p for p in players if player_lower in p['governor_name'].lower()]

                if not matches:
                    await interaction.followup.send(
                        f"❌ No player found matching `{player}`. Try using the autocomplete suggestions!",
                        ephemeral=True
                    )
                    return

                if len(matches) > 1:
                    # Multiple matches - show them
                    match_list = "\n".join([f"• {p['governor_name']} (ID: {p['governor_id']})" for p in matches[:5]])
                    await interaction.followup.send(
                        f"⚠️ Found {len(matches)} players matching `{player}`:\n{match_list}\n\nPlease use `/stats` with the exact Governor ID.",
                        ephemeral=True
                    )
                    return

                # Exact match found
                player_data = matches[0]
                embed = self.create_player_embed(player_data)
                await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Stats command error: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ Error: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="top", description="Show top 10 players by Kill Points Gained")
    @app_commands.describe(
        sort_by="Metric to sort by (default: kill_points_gained)",
        limit="Number of players to show (default: 10, max: 25)"
    )
    @app_commands.choices(sort_by=[
        app_commands.Choice(name="Kill Points Gained", value="kill_points_gained"),
        app_commands.Choice(name="Deaths Gained", value="deads_gained"),
        app_commands.Choice(name="Power", value="power"),
        app_commands.Choice(name="Kill Points", value="kill_points"),
        app_commands.Choice(name="T5 Kills", value="t5_kills"),
        app_commands.Choice(name="T4 Kills", value="t4_kills")
    ])
    async def top(
        self,
        interaction: discord.Interaction,
        sort_by: str = "kill_points_gained",
        limit: int = 10
    ):
        """Show top players"""
        await interaction.response.defer()

        # Limit validation
        limit = min(max(1, limit), 25)

        try:
            url = f"{API_URL}/api/leaderboard?kvk_season_id={self.get_season_id()}&sort_by={sort_by}&limit={limit}"
            logger.info(f"Fetching leaderboard with sort_by={sort_by}, limit={limit}")
            logger.info(f"URL: {url}")

            async with self.session.get(url) as response:
                if response.status != 200:
                    await interaction.followup.send(
                        "❌ Failed to fetch leaderboard. Please try again later.",
                        ephemeral=True
                    )
                    return

                data = await response.json()
                leaderboard = data.get('leaderboard', [])

                if not leaderboard:
                    await interaction.followup.send(
                        "❌ No data available for current KvK season.",
                        ephemeral=True
                    )
                    return

                # Create embed
                sort_labels = {
                    'kill_points_gained': '⚔️ Kill Points Gained',
                    'deads_gained': '☠️ Deaths Gained',
                    'power': '💪 Power',
                    'kill_points': '⚔️ Kill Points',
                    't5_kills': '🎯 T5 Kills',
                    't4_kills': '⚡ T4 Kills'
                }

                embed = discord.Embed(
                    title=f"🏆 Top {limit} Players",
                    description=f"**{sort_labels.get(sort_by, sort_by)}**\nKingdom 3584 • Season {self.get_season_id()}\n━━━━━━━━━━━━━━━━━━━━━━━━",
                    color=discord.Color.gold(),
                    timestamp=datetime.utcnow()
                )

                # Add players to embed
                leaderboard_text = ""
                for i, player in enumerate(leaderboard[:limit], 1):
                    stats = player.get('stats', {})
                    delta = player.get('delta', {})

                    # Get the value we're sorting by
                    if sort_by.endswith('_gained'):
                        field_name = sort_by.replace('_gained', '')
                        value = delta.get(field_name, 0)
                        total_value = stats.get(field_name, 0)
                    else:
                        value = stats.get(sort_by, 0)
                        total_value = value

                    # Rank emoji
                    if i == 1:
                        rank_emoji = "🥇"
                    elif i == 2:
                        rank_emoji = "🥈"
                    elif i == 3:
                        rank_emoji = "🥉"
                    else:
                        rank_emoji = f"**{i}**"

                    # Format with delta if sorting by gained
                    if sort_by.endswith('_gained'):
                        delta_display = self.format_delta(value)
                        value_text = f"`{self.format_number(total_value)}` ({delta_display})"
                    else:
                        value_text = f"`{self.format_number(value)}`"

                    leaderboard_text += f"{rank_emoji} **{player['governor_name']}**\n{value_text}\n\n"

                embed.add_field(
                    name="\u200b",
                    value=leaderboard_text,
                    inline=False
                )

                embed.set_footer(text=f"Last updated: {data.get('current_date', 'N/A')}")
                await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="summary", description="Show kingdom statistics summary")
    async def summary(self, interaction: discord.Interaction):
        """Show kingdom stats summary"""
        await interaction.response.defer()

        try:
            url = f"{API_URL}/api/stats/summary?kvk_season_id={self.get_season_id()}"

            async with self.session.get(url) as response:
                if response.status != 200:
                    await interaction.followup.send(
                        "❌ Failed to fetch summary. Please try again later.",
                        ephemeral=True
                    )
                    return

                data = await response.json()
                summary = data.get('summary', {})
                totals = summary.get('totals', {})
                averages = summary.get('averages', {})
                top_players = summary.get('top_players', {})

                embed = discord.Embed(
                    title="📊 Kingdom 3584 Statistics",
                    description=f"**Season {self.get_season_id()}** • {data.get('player_count', 0)} Players\n━━━━━━━━━━━━━━━━━━━━━━━━",
                    color=discord.Color.purple(),
                    timestamp=datetime.utcnow()
                )

                # Kingdom Totals
                embed.add_field(
                    name="🏰 **Kingdom Totals**",
                    value=f"⚔️ Kill Points: `{self.format_number(totals.get('kill_points', 0))}`\n"
                          f"💪 Power: `{self.format_number(totals.get('power', 0))}`\n"
                          f"🎯 T5 Kills: `{self.format_number(totals.get('t5_kills', 0))}`\n"
                          f"⚡ T4 Kills: `{self.format_number(totals.get('t4_kills', 0))}`",
                    inline=True
                )

                # Averages
                embed.add_field(
                    name="📈 **Per Player Average**",
                    value=f"⚔️ Kill Points: `{self.format_number(averages.get('kill_points', 0))}`\n"
                          f"💪 Power: `{self.format_number(averages.get('power', 0))}`\n"
                          f"🎯 T5 Kills: `{self.format_number(averages.get('t5_kills', 0))}`\n"
                          f"⚡ T4 Kills: `{self.format_number(averages.get('t4_kills', 0))}`",
                    inline=True
                )

                # Empty field for spacing
                embed.add_field(name="\u200b", value="\u200b", inline=False)

                # Top Performers
                top_kp = top_players.get('kill_points', {})
                top_power = top_players.get('power', {})
                top_t5 = top_players.get('t5_kills', {})

                embed.add_field(
                    name="🏆 **Top Performers**",
                    value=f"⚔️ **KP:** {top_kp.get('name', 'N/A')}\n`{self.format_number(top_kp.get('value', 0))}`\n\n"
                          f"💪 **Power:** {top_power.get('name', 'N/A')}\n`{self.format_number(top_power.get('value', 0))}`\n\n"
                          f"🎯 **T5 Kills:** {top_t5.get('name', 'N/A')}\n`{self.format_number(top_t5.get('value', 0))}`",
                    inline=False
                )

                # Dates
                baseline_date = data.get('baseline_date', 'N/A').split('T')[0] if data.get('baseline_date') else 'N/A'
                current_date = data.get('current_date', 'N/A').split('T')[0] if data.get('current_date') else 'N/A'

                embed.add_field(
                    name="📅 **Data Period**",
                    value=f"**Baseline:** {baseline_date}\n**Last Update:** {current_date}",
                    inline=False
                )

                embed.set_footer(text="Kingdom 3584 KvK Tracker")
                await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="compare", description="Compare two players")
    @app_commands.describe(
        player1_id="First player's Governor ID",
        player2_id="Second player's Governor ID"
    )
    async def compare(
        self,
        interaction: discord.Interaction,
        player1_id: str,
        player2_id: str
    ):
        """Compare two players"""
        await interaction.response.defer()

        try:
            # Fetch both players
            url1 = f"{API_URL}/api/player/{player1_id}?kvk_season_id={self.get_season_id()}"
            url2 = f"{API_URL}/api/player/{player2_id}?kvk_season_id={self.get_season_id()}"

            async with self.session.get(url1) as response1:
                if response1.status != 200:
                    await interaction.followup.send(
                        f"❌ Player 1 (ID: {player1_id}) not found.",
                        ephemeral=True
                    )
                    return
                data1 = await response1.json()
                player1 = data1.get('player', data1)

            async with self.session.get(url2) as response2:
                if response2.status != 200:
                    await interaction.followup.send(
                        f"❌ Player 2 (ID: {player2_id}) not found.",
                        ephemeral=True
                    )
                    return
                data2 = await response2.json()
                player2 = data2.get('player', data2)

            # Create comparison embed
            embed = discord.Embed(
                title="⚔️ Player Comparison",
                description=f"**{player1['governor_name']}** vs **{player2['governor_name']}**\n"
                           f"Rank: #{player1.get('rank', 'N/A')} vs #{player2.get('rank', 'N/A')}\n"
                           f"━━━━━━━━━━━━━━━━━━━━━━━━",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )

            stats1 = player1.get('stats', {})
            stats2 = player2.get('stats', {})
            delta1 = player1.get('delta', {})
            delta2 = player2.get('delta', {})

            # Compare metrics with deltas
            metrics = [
                ('⚔️ Kill Points', 'kill_points'),
                ('💪 Power', 'power'),
                ('☠️ Deaths', 'deads'),
                ('🎯 T5 Kills', 't5_kills'),
                ('⚡ T4 Kills', 't4_kills'),
            ]

            for metric_name, field in metrics:
                val1_stat = stats1.get(field, 0)
                val2_stat = stats2.get(field, 0)
                val1_delta = delta1.get(field, 0)
                val2_delta = delta2.get(field, 0)

                diff = val1_stat - val2_stat
                winner = "🟢" if diff > 0 else ("🔴" if diff < 0 else "⚪")

                delta1_display = self.format_delta(val1_delta)
                delta2_display = self.format_delta(val2_delta)

                embed.add_field(
                    name=f"**{metric_name}**",
                    value=f"{winner} `{self.format_number(val1_stat)}` ({delta1_display})\n"
                          f"     vs\n"
                          f"     `{self.format_number(val2_stat)}` ({delta2_display})",
                    inline=True
                )

            # Empty field for better layout
            embed.add_field(name="\u200b", value="\u200b", inline=True)

            embed.set_footer(text="Kingdom 3584 KvK Tracker")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="help", description="Show bot commands and usage")
    async def help_command(self, interaction: discord.Interaction):
        """Show help information"""
        await interaction.response.defer(ephemeral=True)

        embed = discord.Embed(
            title="📖 Kingdom 3584 KvK Tracker Bot",
            description="Track your KvK performance with powerful commands!\n━━━━━━━━━━━━━━━━━━━━━━━━",
            color=discord.Color.blue()
        )

        # Stats command - Updated with autocomplete
        embed.add_field(
            name="⚔️ **/stats <player>**",
            value="View complete KvK statistics with **autocomplete**:\n\n"
                  "**Features:**\n"
                  "• 🔍 **Smart autocomplete** - Search by name or ID\n"
                  "• 📊 **Full stats** - KP, Power, Deaths, T5/T4 Kills\n"
                  "• 🏆 **Current rank** with medal emoji\n"
                  "• 🟢🔴 **Color-coded deltas** (gained stats)\n"
                  "• 🔢 **Readable numbers** - 1.2B, 850M format\n\n"
                  "**Examples:**\n"
                  "• `/stats shino` → search by name\n"
                  "• `/stats 51540567` → search by ID\n━━━━━━━━━━━━━━━━━━━━━━━━",
            inline=False
        )

        # Top command - Updated with all sort options
        embed.add_field(
            name="🏆 **/top [sort_by] [limit]**",
            value="Display top players leaderboard with flexible sorting:\n\n"
                  "**Sort Options:**\n"
                  "• `kill_points_gained` - KP gained (⚔️ default)\n"
                  "• `deaths_gained` - Deaths gained (☠️)\n"
                  "• `t5_kills_gained` - T5 kills gained (🎯)\n"
                  "• `t4_kills_gained` - T4 kills gained (⚡)\n"
                  "• `power` - Total power (💪)\n"
                  "• `kill_points` - Total kill points (⚔️)\n"
                  "• `t5_kills` - Total T5 kills (🎯)\n"
                  "• `t4_kills` - Total T4 kills (⚡)\n\n"
                  "**Limit:** 1-25 players (default: 10)\n\n"
                  "**Examples:**\n"
                  "• `/top` - Top 10 by KP gained\n"
                  "• `/top power 25` - Top 25 by power\n"
                  "• `/top t5_kills_gained 15` - Top 15 T5 farmers\n━━━━━━━━━━━━━━━━━━━━━━━━",
            inline=False
        )

        # Summary command
        embed.add_field(
            name="📊 **/summary**",
            value="Kingdom-wide statistics overview:\n"
                  "• 🏰 **Total kingdom stats** - Combined KP, Power, Kills\n"
                  "• 📈 **Per-player averages** - Average stats per governor\n"
                  "• 🏆 **Top performers** - Best in each category\n"
                  "• 📅 **Data period** - Baseline & last update dates\n\n"
                  "**Example:** `/summary`\n━━━━━━━━━━━━━━━━━━━━━━━━",
            inline=False
        )

        # Compare command
        embed.add_field(
            name="⚔️ **/compare <player1_id> <player2_id>**",
            value="Compare two players side-by-side:\n"
                  "• 📊 **All stats** with deltas shown\n"
                  "• 🏅 **Winner indicators** for each metric\n"
                  "• 🏆 **Rank comparison** - Who's higher?\n"
                  "• 💡 **Head-to-head** battle analysis\n\n"
                  "**Example:** `/compare 53242709 51540567`\n━━━━━━━━━━━━━━━━━━━━━━━━",
            inline=False
        )

        # History command - NEW
        embed.add_field(
            name="📜 **/history [limit]** ✨ NEW!",
            value="View recent upload history for the season:\n"
                  "• 📅 **Upload dates** - When data was collected\n"
                  "• 📝 **Descriptions** - What each upload represents\n"
                  "• 👥 **Player counts** - Active players tracked\n"
                  "• ⚔️ **Total gains** - Kingdom-wide KP/Deaths/Kills\n\n"
                  "**Limit:** 1-10 uploads (default: 5)\n"
                  "**Note:** For full history, visit the website!\n\n"
                  "**Example:** `/history 5`\n━━━━━━━━━━━━━━━━━━━━━━━━",
            inline=False
        )

        # Timeline command
        embed.add_field(
            name="📈 **/timeline <player>**",
            value="Track player progress over time:\n"
                  "• 📊 **Baseline** - Starting point stats\n"
                  "• 📈 **Recent snapshots** - Last 5 uploads\n"
                  "• 🏆 **Rank changes** - How rank evolved\n"
                  "• ⚔️ **Growth stats** - Total KP gained\n"
                  "• 🔍 **Autocomplete** - Search by name or ID\n\n"
                  "**Example:** `/timeline shino`\n━━━━━━━━━━━━━━━━━━━━━━━━",
            inline=False
        )

        # DKP command - NEW
        embed.add_field(
            name="💎 **/dkp [limit]** ✨ NEW!",
            value="View DKP contribution leaderboard:\n"
                  "• ⚔️ **Kills gained** - T4/T5 gained during KvK\n"
                  "• 💎 **DKP scoring** - T5 kills × 2 DKP, T4 kills × 1 DKP\n"
                  "• 🏆 **Top contributors** - Who's killing most\n"
                  "• 📊 **Delta/gained kills only** - Not total kills\n\n"
                  "**Limit:** 1-25 players (default: 10)\n\n"
                  "**Example:** `/dkp 15`\n━━━━━━━━━━━━━━━━━━━━━━━━",
            inline=False
        )

        # Classification command - NEW
        embed.add_field(
            name="👤 **/classification <player>** ✨ NEW!",
            value="View player account classification:\n"
                  "• 👑 **Main accounts** - Primary players\n"
                  "• 🌾 **Farm accounts** - Linked to mains\n"
                  "• 🏖️ **Vacation mode** - Inactive players\n"
                  "• 🔗 **Farm links** - See which farms belong to which main\n"
                  "• 🔍 **Autocomplete** - Search by name or ID\n\n"
                  "**Example:** `/classification shino`\n━━━━━━━━━━━━━━━━━━━━━━━━",
            inline=False
        )

        # Season command - NEW
        embed.add_field(
            name="🏆 **/season** ✨ NEW!",
            value="Show current KvK season information:\n"
                  "• 📅 **Dates** - Start and end dates\n"
                  "• 🟢 **Status** - Active, completed, or archived\n"
                  "• 📊 **Final data** - Check if comprehensive stats uploaded\n"
                  "• 🔢 **Season tracking** - Know which season is active\n\n"
                  "**Example:** `/season`\n━━━━━━━━━━━━━━━━━━━━━━━━",
            inline=False
        )

        # Additional info - Updated
        embed.add_field(
            name="💡 Pro Tips",
            value="• 🔍 **Use autocomplete!** Start typing names in commands\n"
                  "• 🎯 **Find Governor ID:** In-game → Tap your avatar\n"
                  "• 📊 **Deltas:** Show change since baseline (starting point)\n"
                  "• 🟢 **Green** = Positive change (good for KP, bad for deaths)\n"
                  "• 🔴 **Red** = Negative change\n"
                  "• 🔄 **Data updates:** When admin uploads new scans\n"
                  "• 🌐 **Web version:** https://kd3584-production.up.railway.app\n━━━━━━━━━━━━━━━━━━━━━━━━",
            inline=False
        )

        # Links section
        embed.add_field(
            name="🔗 Useful Links",
            value="• 🌐 **Leaderboard:** [kd-3584.vercel.app](https://kd-3584.vercel.app)\n"
                  "• 🔧 **API Status:** [Railway Dashboard](https://kd3584-production.up.railway.app/)\n"
                  "• 📖 **Full Documentation:** Type `/help` anytime",
            inline=False
        )

        embed.set_footer(text="Kingdom 3584 KvK Tracker • Season 1")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="history", description="View upload history for the current season")
    @app_commands.describe(limit="Number of recent uploads to show (default: 5)")
    async def history(self, interaction: discord.Interaction, limit: int = 5):
        """Show upload history for the season"""
        await interaction.response.defer()

        try:
            # Limit to reasonable range (max 10 for Discord)
            limit = max(1, min(limit, 10))

            url = f"{API_URL}/api/history?kvk_season_id={self.get_season_id()}&limit={limit}"

            async with self.session.get(url) as response:
                if response.status != 200:
                    await interaction.followup.send(
                        "❌ No upload history found for this season.",
                        ephemeral=True
                    )
                    return

                data = await response.json()
                uploads = data.get('uploads', [])

                if not uploads:
                    await interaction.followup.send(
                        "❌ No upload history found for this season.",
                        ephemeral=True
                    )
                    return

                embed = discord.Embed(
                    title=f"📜 Upload History",
                    description=f"Recent {len(uploads)} uploads for Season {self.get_season_id()}\n━━━━━━━━━━━━━━━━━━━━━━━━",
                    color=discord.Color.purple(),
                    timestamp=datetime.utcnow()
                )

                for upload in uploads:
                    timestamp = upload.get('timestamp')
                    if timestamp:
                        # Format timestamp nicely
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if isinstance(timestamp, str) else timestamp
                        date_str = dt.strftime('%b %d, %H:%M')
                    else:
                        date_str = 'Unknown date'

                    description = upload.get('description', 'No description')
                    player_count = upload.get('player_count', 0)

                    summary = upload.get('summary', {})
                    total_kp_gained = summary.get('total_kill_points_gained', 0)
                    total_deads_gained = summary.get('total_deads_gained', 0)
                    total_t5_gained = summary.get('total_t5_kills_gained', 0)
                    total_t4_gained = summary.get('total_t4_kills_gained', 0)

                    # Build compact stats display
                    stats_lines = []
                    if total_kp_gained > 0:
                        stats_lines.append(f"⚔️ KP: {self.format_number(total_kp_gained)}")
                    if total_deads_gained > 0:
                        stats_lines.append(f"☠️ Deaths: {self.format_number(total_deads_gained)}")
                    if total_t5_gained > 0:
                        stats_lines.append(f"🎯 T5: {self.format_number(total_t5_gained)}")
                    if total_t4_gained > 0:
                        stats_lines.append(f"⚡ T4: {self.format_number(total_t4_gained)}")

                    stats_text = " • ".join(stats_lines) if stats_lines else "No delta data"

                    embed.add_field(
                        name=f"{date_str}",
                        value=f"📝 {description}\n"
                              f"👥 {player_count} players\n"
                              f"{stats_text}\n\u200b",
                        inline=False
                    )

                embed.set_footer(text="Kingdom 3584 KvK Tracker • Season 1")
                await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"History command error: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ Error: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="timeline", description="View a player's progress timeline")
    @app_commands.describe(player="Search by player name or Governor ID")
    @app_commands.autocomplete(player=player_autocomplete)
    async def timeline(self, interaction: discord.Interaction, player: str):
        """Show player progress over time"""
        await interaction.response.defer()

        try:
            # First, try as governor_id
            url = f"{API_URL}/api/player/{player}/timeline?kvk_season_id={self.get_season_id()}"

            async with self.session.get(url) as response:
                if response.status != 200:
                    # Try searching by name
                    search_url = f"{API_URL}/api/leaderboard?kvk_season_id={self.get_season_id()}&limit=500"
                    async with self.session.get(search_url) as search_response:
                        if search_response.status != 200:
                            await interaction.followup.send(
                                "❌ Failed to fetch timeline. Please try again later.",
                                ephemeral=True
                            )
                            return

                        search_data = await search_response.json()
                        players = search_data.get('leaderboard', [])
                        player_lower = player.lower().strip()
                        matches = [p for p in players if player_lower in p['governor_name'].lower()]

                        if not matches:
                            await interaction.followup.send(
                                f"❌ No player found matching `{player}`.",
                                ephemeral=True
                            )
                            return

                        if len(matches) > 1:
                            match_list = "\n".join([f"• {p['governor_name']} (ID: {p['governor_id']})" for p in matches[:5]])
                            await interaction.followup.send(
                                f"⚠️ Found {len(matches)} players matching `{player}`:\n{match_list}\n\nPlease use `/timeline` with the exact Governor ID.",
                                ephemeral=True
                            )
                            return

                        # Retry with correct ID
                        governor_id = matches[0]['governor_id']
                        url = f"{API_URL}/api/player/{governor_id}/timeline?kvk_season_id={self.get_season_id()}"
                        response = await self.session.get(url)

                data = await response.json()

                if not data.get('success'):
                    await interaction.followup.send(
                        f"❌ {data.get('error', 'No timeline data found')}",
                        ephemeral=True
                    )
                    return

                governor_name = data.get('governor_name', 'Unknown')
                governor_id = data.get('governor_id', 'Unknown')
                timeline = data.get('timeline', [])
                baseline = data.get('baseline')

                if not timeline:
                    await interaction.followup.send(
                        f"❌ No timeline data found for {governor_name}.",
                        ephemeral=True
                    )
                    return

                embed = discord.Embed(
                    title=f"📈 Progress Timeline",
                    description=f"**{governor_name}** (ID: {governor_id})\nSeason {self.get_season_id()} • {len(timeline)} snapshots\n━━━━━━━━━━━━━━━━━━━━━━━━",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )

                # Add baseline if available
                if baseline:
                    baseline_stats = baseline.get('stats', {})
                    embed.add_field(
                        name="📊 Baseline (Starting Point)",
                        value=f"⚔️ KP: `{self.format_number(baseline_stats.get('kill_points', 0))}`\n"
                              f"💪 Power: `{self.format_number(baseline_stats.get('power', 0))}`\n\u200b",
                        inline=False
                    )

                # Show most recent 5 snapshots
                for i, snapshot in enumerate(timeline[-5:], 1):
                    timestamp = snapshot.get('timestamp')
                    if timestamp:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if isinstance(timestamp, str) else timestamp
                        date_str = dt.strftime('%b %d, %H:%M')
                    else:
                        date_str = 'Unknown date'

                    stats = snapshot.get('stats', {})
                    delta = snapshot.get('delta', {})
                    rank = snapshot.get('rank', 'N/A')
                    file_name = snapshot.get('file_name', 'Unknown')
                    description = snapshot.get('description', '')

                    kp_delta = self.format_delta(delta.get('kill_points', 0))

                    embed.add_field(
                        name=f"#{rank} • {file_name}",
                        value=f"📅 {date_str} - {description}\n"
                              f"⚔️ KP: `{self.format_number(stats.get('kill_points', 0))}` {kp_delta}\n"
                              f"💪 Power: `{self.format_number(stats.get('power', 0))}`\n\u200b",
                        inline=False
                    )

                # Add summary at the end
                first_snapshot = timeline[0]
                last_snapshot = timeline[-1]
                first_stats = first_snapshot.get('stats', {})
                last_stats = last_snapshot.get('stats', {})

                kp_growth = last_stats.get('kill_points', 0) - first_stats.get('kill_points', 0)
                rank_first = first_snapshot.get('rank', 0)
                rank_last = last_snapshot.get('rank', 0)
                rank_change = rank_first - rank_last

                embed.add_field(
                    name="📊 Overall Progress",
                    value=f"⚔️ Total KP Gained: `{self.format_number(kp_growth)}`\n"
                          f"🏆 Rank Change: **{rank_first}** → **{rank_last}** "
                          f"({'🟢 +' + str(rank_change) if rank_change > 0 else '🔴 ' + str(rank_change) if rank_change < 0 else 'No change'})\n"
                          f"📈 Snapshots Tracked: {len(timeline)}",
                    inline=False
                )

                embed.set_footer(text=f"Kingdom 3584 KvK Tracker • Showing last 5 of {len(timeline)} snapshots")
                await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Timeline command error: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ Error: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="dkp", description="Show DKP contribution leaderboard")
    @app_commands.describe(
        limit="Number of players to show (default: 10, max: 25)"
    )
    async def dkp(self, interaction: discord.Interaction, limit: int = 10):
        """Show DKP contribution leaderboard"""
        await interaction.response.defer()

        # Limit validation
        limit = min(max(1, limit), 25)

        try:
            url = f"{API_URL}/api/verified-deaths/contribution-scores/{self.get_season_id()}?limit={limit}"
            logger.info(f"Fetching DKP leaderboard with limit={limit}")

            async with self.session.get(url) as response:
                if response.status != 200:
                    await interaction.followup.send(
                        "❌ No DKP contribution data available yet. Verified deaths need to be uploaded first.",
                        ephemeral=True
                    )
                    return

                data = await response.json()
                contributions = data.get('contributions', [])

                if not contributions:
                    await interaction.followup.send(
                        "❌ No DKP contribution data available for current season.",
                        ephemeral=True
                    )
                    return

                # Create embed
                embed = discord.Embed(
                    title=f"🏆 Top {limit} DKP Contributors",
                    description=f"**T4/T5 Kills Gained During KvK**\nKingdom 3584 • Season {self.get_season_id()}\n━━━━━━━━━━━━━━━━━━━━━━━━",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )

                # Add players to embed
                leaderboard_text = ""
                for i, contribution in enumerate(contributions[:limit], 1):
                    dkp_score = contribution.get('total_contribution_score', 0)
                    t5_kills_gained = contribution.get('t5_kills_gained', 0)
                    t4_kills_gained = contribution.get('t4_kills_gained', 0)
                    governor_name = contribution.get('governor_name', 'Unknown')

                    # Rank emoji
                    if i == 1:
                        rank_emoji = "🥇"
                    elif i == 2:
                        rank_emoji = "🥈"
                    elif i == 3:
                        rank_emoji = "🥉"
                    else:
                        rank_emoji = f"**{i}**"

                    leaderboard_text += f"{rank_emoji} **{governor_name}**\n"
                    leaderboard_text += f"💎 DKP: `{self.format_number(dkp_score)}`"

                    if t5_kills_gained > 0 or t4_kills_gained > 0:
                        leaderboard_text += f" (T5: {self.format_number(t5_kills_gained)}, T4: {self.format_number(t4_kills_gained)})\n\n"
                    else:
                        leaderboard_text += "\n\n"

                embed.add_field(
                    name="\u200b",
                    value=leaderboard_text,
                    inline=False
                )

                # Add legend
                embed.add_field(
                    name="📊 DKP Calculation",
                    value="• T5 Kills Gained × 2 DKP\n• T4 Kills Gained × 1 DKP\n• Shows kills gained during KvK only",
                    inline=False
                )

                embed.set_footer(text=f"Contribution scores based on gained kills")
                await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"DKP command error: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ Error: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="classification", description="View player account classification")
    @app_commands.describe(player="Search by player name or Governor ID")
    @app_commands.autocomplete(player=player_autocomplete)
    async def classification(self, interaction: discord.Interaction, player: str):
        """Show player classification (main/farm/vacation)"""
        await interaction.response.defer()

        try:
            # Try to get classification by ID
            url = f"{API_URL}/api/players/classification/{self.get_season_id()}/{player}"

            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()

                    governor_name = data.get('governor_name', 'Unknown')
                    governor_id = data.get('governor_id', player)
                    account_type = data.get('account_type', 'main')
                    linked_to_main = data.get('linked_to_main')
                    farm_accounts = data.get('farm_accounts', [])

                    # Create embed
                    embed = discord.Embed(
                        title=f"👤 Account Classification",
                        description=f"**{governor_name}** (ID: {governor_id})\n━━━━━━━━━━━━━━━━━━━━━━━━",
                        color=discord.Color.green() if account_type == 'main' else discord.Color.orange(),
                        timestamp=datetime.utcnow()
                    )

                    # Account type
                    type_emoji = {
                        'main': '👑',
                        'farm': '🌾',
                        'vacation': '🏖️'
                    }
                    type_display = {
                        'main': 'Main Account',
                        'farm': 'Farm Account',
                        'vacation': 'Vacation Mode'
                    }

                    embed.add_field(
                        name="Account Type",
                        value=f"{type_emoji.get(account_type, '❓')} **{type_display.get(account_type, account_type.title())}**",
                        inline=False
                    )

                    # If it's a farm, show main account
                    if account_type == 'farm' and linked_to_main:
                        embed.add_field(
                            name="🔗 Linked to Main",
                            value=f"Governor ID: `{linked_to_main}`",
                            inline=False
                        )

                    # If it's a main, show farm accounts
                    if account_type == 'main' and farm_accounts:
                        farm_list = "\n".join([f"• `{farm_id}`" for farm_id in farm_accounts[:5]])
                        if len(farm_accounts) > 5:
                            farm_list += f"\n• ... and {len(farm_accounts) - 5} more"

                        embed.add_field(
                            name=f"🌾 Farm Accounts ({len(farm_accounts)})",
                            value=farm_list,
                            inline=False
                        )

                    embed.set_footer(text="Kingdom 3584 KvK Tracker")
                    await interaction.followup.send(embed=embed)
                    return

            # If not found by ID, search by name
            search_url = f"{API_URL}/api/leaderboard?kvk_season_id={self.get_season_id()}&limit=500"
            async with self.session.get(search_url) as search_response:
                if search_response.status != 200:
                    await interaction.followup.send(
                        "❌ Failed to fetch player data.",
                        ephemeral=True
                    )
                    return

                search_data = await search_response.json()
                players = search_data.get('leaderboard', [])
                player_lower = player.lower().strip()
                matches = [p for p in players if player_lower in p['governor_name'].lower()]

                if not matches:
                    await interaction.followup.send(
                        f"❌ No player found matching `{player}`.",
                        ephemeral=True
                    )
                    return

                if len(matches) > 1:
                    match_list = "\n".join([f"• {p['governor_name']} (ID: {p['governor_id']})" for p in matches[:5]])
                    await interaction.followup.send(
                        f"⚠️ Found {len(matches)} players matching `{player}`:\n{match_list}\n\nPlease use `/classification` with the exact Governor ID.",
                        ephemeral=True
                    )
                    return

                # Retry with correct ID
                governor_id = matches[0]['governor_id']
                url = f"{API_URL}/api/players/classification/{self.get_season_id()}/{governor_id}"
                async with self.session.get(url) as retry_response:
                    if retry_response.status == 200:
                        # Re-run the same logic
                        data = await retry_response.json()
                        # ... (same embed creation logic as above)
                        await interaction.followup.send(
                            f"Player `{player}` has not been classified yet. Default: Main Account",
                            ephemeral=True
                        )
                    else:
                        await interaction.followup.send(
                            f"Player `{matches[0]['governor_name']}` has not been classified yet. Default: Main Account",
                            ephemeral=True
                        )

        except Exception as e:
            logger.error(f"Classification command error: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ Error: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="season", description="Show current KvK season information")
    async def season_info(self, interaction: discord.Interaction):
        """Show current season info"""
        await interaction.response.defer()

        try:
            url = f"{API_URL}/api/seasons/active"

            async with self.session.get(url) as response:
                if response.status != 200:
                    await interaction.followup.send(
                        "❌ No active season found.",
                        ephemeral=True
                    )
                    return

                data = await response.json()

                season_id = data.get('season_id', 'Unknown')
                start_date = data.get('start_date', 'Unknown')
                end_date = data.get('end_date', 'N/A')
                status = data.get('status', 'active')
                final_data_uploaded = data.get('final_data_uploaded', False)

                # Format dates
                if start_date and start_date != 'Unknown':
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    start_str = start_dt.strftime('%B %d, %Y')
                else:
                    start_str = 'Unknown'

                if end_date and end_date != 'N/A':
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    end_str = end_dt.strftime('%B %d, %Y')
                else:
                    end_str = 'Ongoing'

                # Status emoji
                status_emoji = {
                    'active': '🟢',
                    'completed': '✅',
                    'archived': '📦'
                }

                embed = discord.Embed(
                    title=f"🏆 Current KvK Season",
                    description=f"**{season_id.replace('_', ' ').title()}**\n━━━━━━━━━━━━━━━━━━━━━━━━",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )

                embed.add_field(
                    name="Status",
                    value=f"{status_emoji.get(status, '❓')} **{status.title()}**",
                    inline=True
                )

                embed.add_field(
                    name="Start Date",
                    value=start_str,
                    inline=True
                )

                embed.add_field(
                    name="End Date",
                    value=end_str,
                    inline=True
                )

                if final_data_uploaded:
                    embed.add_field(
                        name="📊 Final Data",
                        value="✅ Uploaded (Comprehensive stats available)",
                        inline=False
                    )

                embed.set_footer(text="Kingdom 3584 KvK Tracker")
                await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Season info command error: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ Error: {str(e)}",
                ephemeral=True
            )


@bot.event
async def on_ready():
    """Bot startup event"""
    print(f'✅ Logged in as {bot.user} (ID: {bot.user.id})')
    print(f'📊 Connected to {len(bot.guilds)} guilds')

    # List all guilds
    for guild in bot.guilds:
        print(f'   - {guild.name} (ID: {guild.id})')

    print('🚀 Bot is ready!')

    # Clear all guild commands and sync globally to force cache refresh
    try:
        # First, clear guild-specific commands from all guilds
        for guild in bot.guilds:
            try:
                bot.tree.clear_commands(guild=discord.Object(id=guild.id))
                await bot.tree.sync(guild=discord.Object(id=guild.id))
                print(f'🗑️  Cleared guild commands for: {guild.name}')
            except Exception as e:
                print(f'❌ Failed to clear guild commands for {guild.name}: {e}')

        # Now sync commands globally (will take effect in 1 hour, but clears cache)
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} command(s) globally')
        print('⏳ Global commands will be available in all servers within 1 hour')
        print('💡 To see commands immediately, kick and re-invite the bot')

    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')


@bot.event
async def on_guild_join(guild):
    """Handle when bot joins a new guild"""
    print(f'🎉 Joined new guild: {guild.name} (ID: {guild.id})')
    print('✅ Commands will be available via global sync (already synced)')


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Global error handler for slash commands"""
    logger.error(f"Command error: {error}", exc_info=error)

    # Handle specific error types
    if isinstance(error, app_commands.CommandInvokeError):
        original_error = error.original

        # Handle webhook timeout errors gracefully
        if isinstance(original_error, discord.errors.NotFound):
            logger.warning(f"Webhook timeout for command: {interaction.command.name if interaction.command else 'unknown'}")
            # Don't try to respond - the interaction has already timed out
            return

        error_message = "❌ An error occurred while processing your command. Please try again."
    else:
        error_message = f"❌ Error: {str(error)}"

    # Try to send error message if interaction hasn't expired
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(error_message, ephemeral=True)
        else:
            await interaction.followup.send(error_message, ephemeral=True)
    except discord.errors.NotFound:
        # Interaction has expired, log it
        logger.warning("Could not send error message - interaction expired")
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")


async def main():
    """Main function"""
    async with bot:
        await bot.add_cog(KvKBot(bot))
        await bot.start(DISCORD_TOKEN)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
