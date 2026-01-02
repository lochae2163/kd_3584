import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp
import os
from datetime import datetime
from typing import Optional
import logging

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
        """Format number with commas"""
        if num >= 1_000_000_000:
            return f"{num / 1_000_000_000:.2f}B"
        elif num >= 1_000_000:
            return f"{num / 1_000_000:.2f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.2f}K"
        return str(num)

    def format_delta(self, value):
        """Format delta value with color indicators

        Args:
            value: The delta value to format

        Returns:
            Green circle for positive (+), red circle for negative (-)
        """
        if value == 0:
            return f"{self.format_number(value)}"
        elif value > 0:
            # Positive change = green
            return f"🟢 +{self.format_number(value)}"
        else:
            # Negative change = red
            return f"🔴 {self.format_number(value)}"

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

        # Current Stats with color-coded deltas - 2 per row for better spacing
        embed.add_field(
            name="⚔️ **Kill Points**",
            value=f"```yaml\nTotal: {self.format_number(stats.get('kill_points', 0))}```\n{self.format_delta(delta.get('kill_points', 0))}\n",
            inline=True
        )

        embed.add_field(
            name="💪 **Power**",
            value=f"```yaml\nTotal: {self.format_number(stats.get('power', 0))}```\n{self.format_delta(delta.get('power', 0))}\n",
            inline=True
        )

        # Empty field for spacing
        embed.add_field(name="\u200b", value="\u200b", inline=False)

        embed.add_field(
            name="☠️ **Deaths**",
            value=f"```yaml\nTotal: {self.format_number(stats.get('deads', 0))}```\n{self.format_delta(delta.get('deads', 0))}\n",
            inline=True
        )

        embed.add_field(
            name="🎯 **T5 Kills**",
            value=f"```yaml\nTotal: {self.format_number(stats.get('t5_kills', 0))}```\n{self.format_delta(delta.get('t5_kills', 0))}\n",
            inline=True
        )

        # Empty field for spacing
        embed.add_field(name="\u200b", value="\u200b", inline=False)

        embed.add_field(
            name="⚡ **T4 Kills**",
            value=f"```yaml\nTotal: {self.format_number(stats.get('t4_kills', 0))}```\n{self.format_delta(delta.get('t4_kills', 0))}\n",
            inline=True
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
                    title=f"🏆 Top {limit} - {sort_labels.get(sort_by, sort_by)}",
                    description=f"Kingdom 3584 • Season {KVK_SEASON_ID}",
                    color=discord.Color.gold(),
                    timestamp=datetime.utcnow()
                )

                # Add players to embed
                for i, player in enumerate(leaderboard[:limit], 1):
                    stats = player.get('stats', {})
                    delta = player.get('delta', {})

                    # Get the value we're sorting by
                    if sort_by.endswith('_gained'):
                        field_name = sort_by.replace('_gained', '')
                        value = delta.get(field_name, 0)
                    else:
                        value = stats.get(sort_by, 0)

                    # Rank emoji
                    if i == 1:
                        rank_emoji = "🥇"
                    elif i == 2:
                        rank_emoji = "🥈"
                    elif i == 3:
                        rank_emoji = "🥉"
                    else:
                        rank_emoji = f"**{i}.**"

                    embed.add_field(
                        name=f"{rank_emoji} {player['governor_name']}",
                        value=f"**{self.format_number(value)}** • ID: {player['governor_id']}",
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
                    description=f"**Season:** {KVK_SEASON_ID} • **Players:** {data.get('player_count', 0)}",
                    color=discord.Color.purple(),
                    timestamp=datetime.utcnow()
                )

                # Kingdom Totals
                embed.add_field(
                    name="🏰 Kingdom Totals",
                    value=f"**KP:** {self.format_number(totals.get('kill_points', 0))}\n"
                          f"**Power:** {self.format_number(totals.get('power', 0))}\n"
                          f"**T5 Kills:** {self.format_number(totals.get('t5_kills', 0))}\n"
                          f"**T4 Kills:** {self.format_number(totals.get('t4_kills', 0))}",
                    inline=True
                )

                # Averages
                embed.add_field(
                    name="📈 Per Player Average",
                    value=f"**KP:** {self.format_number(averages.get('kill_points', 0))}\n"
                          f"**Power:** {self.format_number(averages.get('power', 0))}\n"
                          f"**T5 Kills:** {self.format_number(averages.get('t5_kills', 0))}\n"
                          f"**T4 Kills:** {self.format_number(averages.get('t4_kills', 0))}",
                    inline=True
                )

                # Top Performers
                top_kp = top_players.get('kill_points', {})
                top_power = top_players.get('power', {})
                top_t5 = top_players.get('t5_kills', {})

                embed.add_field(
                    name="🏆 Top Performers",
                    value=f"**KP:** {top_kp.get('name', 'N/A')} ({self.format_number(top_kp.get('value', 0))})\n"
                          f"**Power:** {top_power.get('name', 'N/A')} ({self.format_number(top_power.get('value', 0))})\n"
                          f"**T5 Kills:** {top_t5.get('name', 'N/A')} ({self.format_number(top_t5.get('value', 0))})",
                    inline=False
                )

                # Dates
                embed.add_field(
                    name="📅 Data Period",
                    value=f"**Baseline:** {data.get('baseline_date', 'N/A')}\n"
                          f"**Last Update:** {data.get('current_date', 'N/A')}",
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
                description=f"**{player1['governor_name']}** vs **{player2['governor_name']}**",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )

            stats1 = player1.get('stats', {})
            stats2 = player2.get('stats', {})
            delta1 = player1.get('delta', {})
            delta2 = player2.get('delta', {})

            # Compare metrics
            metrics = [
                ('Kill Points', 'kill_points'),
                ('KP Gained', 'kill_points', True),
                ('Power', 'power'),
                ('T5 Kills', 't5_kills'),
                ('T4 Kills', 't4_kills'),
                ('Deaths', 'deads')
            ]

            for metric_name, field, *is_delta in metrics:
                if is_delta:
                    val1 = delta1.get(field, 0)
                    val2 = delta2.get(field, 0)
                else:
                    val1 = stats1.get(field, 0)
                    val2 = stats2.get(field, 0)

                diff = val1 - val2
                winner = "🟢" if diff > 0 else ("🔴" if diff < 0 else "⚪")

                embed.add_field(
                    name=f"{metric_name}",
                    value=f"{winner} {self.format_number(val1)} vs {self.format_number(val2)}\n"
                          f"Diff: {'+' if diff >= 0 else ''}{self.format_number(diff)}",
                    inline=True
                )

            # Rankings
            embed.add_field(
                name="🏆 Rank",
                value=f"#{player1.get('rank', 'N/A')} vs #{player2.get('rank', 'N/A')}",
                inline=False
            )

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
            description="Get your KvK stats directly in Discord!",
            color=discord.Color.blue()
        )

        commands_list = [
            ("**/stats <governor_id>**", "Get your KvK stats\nExample: `/stats 53242709`"),
            ("**/top [sort_by] [limit]**", "Show top players\nExample: `/top kill_points_gained 10`"),
            ("**/summary**", "Show kingdom statistics"),
            ("**/compare <id1> <id2>**", "Compare two players\nExample: `/compare 53242709 51540567`"),
            ("**/help**", "Show this help message")
        ]

        for cmd, desc in commands_list:
            embed.add_field(name=cmd, value=desc, inline=False)

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
    print('🚀 Bot is ready!')

    # Sync commands
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')


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
