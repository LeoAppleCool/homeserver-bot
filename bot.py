import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", intents=intents)


async def load_cogs() -> None:
    for cog in ("cogs.dashboard", "cogs.docker_monitor", "cogs.alerts", "cogs.commands"):
        await bot.load_extension(cog)
        print(f"Loaded {cog}")


@bot.event
async def on_ready() -> None:
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    synced = await bot.tree.sync(guild=guild)
    print(f"Synced {len(synced)} slash command(s) to guild {GUILD_ID}")


async def main() -> None:
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
