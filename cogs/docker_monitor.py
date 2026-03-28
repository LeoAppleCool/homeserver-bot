"""Live Docker container dashboard — updates every 30 seconds by editing a persistent embed."""

import os
from datetime import datetime

import discord
from discord.ext import commands, tasks

from utils.docker_utils import get_containers
from utils.storage import get_message_id, set_message_id

DOCKER_CHANNEL_ID = int(os.getenv("DOCKER_CHANNEL_ID", "0"))


def build_docker_embed(containers: list[dict]) -> discord.Embed:
    running = sum(1 for c in containers if c["running"])
    total = len(containers)

    if not containers:
        color = discord.Color.greyple()
        description = "No containers found — Docker may not be accessible."
    elif running == total:
        color = discord.Color.green()
        description = f"✅ All **{total}** container(s) running"
    elif running == 0:
        color = discord.Color.red()
        description = f"❌ All **{total}** container(s) are down"
    else:
        color = discord.Color.yellow()
        description = f"⚠️ **{running}/{total}** container(s) running"

    embed = discord.Embed(
        title="🐳 Docker Container Status",
        description=description,
        color=color,
        timestamp=datetime.utcnow(),
    )

    for c in containers:
        icon = "✅" if c["running"] else "❌"
        restarts = f"🔁 Restarts: **{c['restart_count']}**" if c["restart_count"] else "🔁 No restarts"
        uptime_label = "Up" if c["running"] else "Status"
        embed.add_field(
            name=f"{icon} {c['name']}",
            value=f"⏱️ {uptime_label}: **{c['uptime']}**\n{restarts}\n📦 `{c['image']}`",
            inline=True,
        )

    embed.set_footer(text="Updates every 30 seconds")
    return embed


class DockerMonitor(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._update_loop.start()

    def cog_unload(self) -> None:
        self._update_loop.cancel()

    @tasks.loop(seconds=30)
    async def _update_loop(self) -> None:
        channel = self.bot.get_channel(DOCKER_CHANNEL_ID)
        if channel is None:
            return

        embed = build_docker_embed(get_containers())
        msg_id = get_message_id("docker_message")

        if msg_id:
            try:
                msg = await channel.fetch_message(msg_id)
                await msg.edit(embed=embed)
                return
            except (discord.NotFound, discord.HTTPException):
                pass

        msg = await channel.send(embed=embed)
        set_message_id("docker_message", msg.id)

    @_update_loop.before_loop
    async def _before(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DockerMonitor(bot))
