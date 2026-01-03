"""
Force sync Discord commands to clear cache

Run this script once to force Discord to update command definitions.
This will clear the global command cache.
"""
import discord
from discord import app_commands
import os
import asyncio

DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

if not DISCORD_TOKEN:
    print("❌ DISCORD_BOT_TOKEN not set!")
    exit(1)

class Client(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Clear all global commands
        self.tree.clear_commands(guild=None)
        await self.tree.sync()
        print("✅ Cleared all global commands")

        # Wait a moment
        await asyncio.sleep(2)

        # Now close
        await self.close()

async def main():
    client = Client()
    await client.start(DISCORD_TOKEN)

if __name__ == '__main__':
    print("🔄 Clearing Discord command cache...")
    asyncio.run(main())
    print("✅ Done! Now restart your bot and wait 1-2 minutes for commands to re-sync.")
