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
KVK_SEASON_ID = os.getenv('KVK_SEASON_ID', 'season_1')
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

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

    async def cog_unload(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()

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
            # Negative change = red
            return f"🔴 ({self.format_number(abs(value))})"

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

    @app_commands.command(name="stats", description="Get your KvK stats by Governor ID")
    @app_commands.describe(governor_id="Your Governor ID (e.g., 53242709)")
    async def stats(self, interaction: discord.Interaction, governor_id: str):
        """Get player stats by Governor ID"""
        await interaction.response.defer()

        try:
            url = f"{API_URL}/api/player/{governor_id}?kvk_season_id={KVK_SEASON_ID}"

            async with self.session.get(url) as response:
                if response.status == 404:
                    await interaction.followup.send(
                        f"❌ Governor ID `{governor_id}` not found in the current KvK season.",
                        ephemeral=True
                    )
                    return

                if response.status != 200:
                    await interaction.followup.send(
                        "❌ Failed to fetch stats. Please try again later.",
                        ephemeral=True
                    )
                    return

                data = await response.json()
                # Extract player data from response
                player_data = data.get('player', data)
                embed = self.create_player_embed(player_data)
                await interaction.followup.send(embed=embed)

        except Exception as e:
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
            url = f"{API_URL}/api/leaderboard?kvk_season_id={KVK_SEASON_ID}&sort_by={sort_by}&limit={limit}"
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
                    description=f"**{sort_labels.get(sort_by, sort_by)}**\nKingdom 3584 • Season {KVK_SEASON_ID}\n━━━━━━━━━━━━━━━━━━━━━━━━",
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
            url = f"{API_URL}/api/stats/summary?kvk_season_id={KVK_SEASON_ID}"

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
                    description=f"**Season {KVK_SEASON_ID}** • {data.get('player_count', 0)} Players\n━━━━━━━━━━━━━━━━━━━━━━━━",
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
            url1 = f"{API_URL}/api/player/{player1_id}?kvk_season_id={KVK_SEASON_ID}"
            url2 = f"{API_URL}/api/player/{player2_id}?kvk_season_id={KVK_SEASON_ID}"

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
            description="Get your KvK stats directly in Discord!\n━━━━━━━━━━━━━━━━━━━━━━━━",
            color=discord.Color.blue()
        )

        # Stats command
        embed.add_field(
            name="⚔️ **/stats <governor_id>**",
            value="View your complete KvK statistics including:\n"
                  "• Kill Points (total and gained)\n"
                  "• Power (total and gained)\n"
                  "• Deaths, T5/T4 Kills\n"
                  "• Current rank\n"
                  "• Color-coded deltas (🟢 positive, 🔴 negative)\n\n"
                  "**Example:** `/stats 53242709` \n━━━━━━━━━━━━━━━━━━━━━━━━",
            inline=False
        )

        # Top command
        embed.add_field(
            name="🏆 **/top [sort_by] [limit]**",
            value="Display top players leaderboard\n\n"
                  "**Sort Options:**\n"
                  "• `kill_points_gained` - KP gained since baseline\n"
                  "• `deaths_gained` - Deaths gained since baseline\n"
                  "• `power` - Total power\n"
                  "• `kill_points` - Total kill points\n"
                  "• `t5_kills` - Total T5 kills\n"
                  "• `t4_kills` - Total T4 kills\n\n"
                  "**Limit:** 1-25 players (default: 10)\n\n"
                  "**Examples:**\n"
                  "`/top kill_points_gained 10`\n"
                  "`/top power 25`\n"
                  "`/top t5_kills 15` \n━━━━━━━━━━━━━━━━━━━━━━━━",
            inline=False
        )

        # Summary command
        embed.add_field(
            name="📊 **/summary**",
            value="Kingdom-wide statistics overview:\n"
                  "• Total kingdom stats\n"
                  "• Per-player averages\n"
                  "• Top performers in each category\n"
                  "• Data collection period\n\n"
                  "**Example:** `/summary`\n━━━━━━━━━━━━━━━━━━━━━━━━",
            inline=False
        )

        # Compare command
        embed.add_field(
            name="⚔️ **/compare <player1_id> <player2_id>**",
            value="Compare two players side-by-side:\n"
                  "• All stats with deltas\n"
                  "• Winner indicators for each metric\n"
                  "• Rank comparison\n\n"
                  "**Example:** `/compare 53242709 51540567`\n━━━━━━━━━━━━━━━━━━━━━━━━",
            inline=False
        )

        # Help command
        embed.add_field(
            name="❓ **/help**",
            value="Show this help message\n━━━━━━━━━━━━━━━━━━━━━━━━",
            inline=False
        )

        # Additional info
        embed.add_field(
            name="💡 Tips",
            value="• Find your Governor ID in-game: Tap your avatar\n"
                  "• All deltas show change since baseline\n"
                  "• 🟢 = positive change, 🔴 = negative change\n"
                  "• Data updates when admin uploads new scans\n━━━━━━━━━━━━━━━━━━━━━━━━",
            inline=False
        )

        embed.add_field(
            name="🔗 Web Dashboard",
            value="[View Full Leaderboard](https://kd-3584.vercel.app)",
            inline=False
        )

        embed.set_footer(text="Kingdom 3584 KvK Tracker • Made with ❤️ for the alliance")
        await interaction.followup.send(embed=embed, ephemeral=True)


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
