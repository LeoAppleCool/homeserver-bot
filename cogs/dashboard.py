"""Live system stats dashboard — updates every 30 seconds by editing a persistent embed."""

import os
from datetime import datetime

import discord
from discord.ext import commands, tasks

from utils.storage import get_message_id, set_message_id
from utils.system_stats import get_all_stats

STATUS_CHANNEL_ID = int(os.getenv("STATUS_CHANNEL_ID", "0"))


def _progress_bar(percent: float, length: int = 12) -> str:
    filled = round(percent / 100 * length)
    return "█" * filled + "░" * (length - filled)


def _status_color(cpu: float, ram: float, disk: float, temp: float | None) -> discord.Color:
    if cpu > 80 or ram > 85 or disk > 90 or (temp is not None and temp > 75):
        return discord.Color.red()
    if cpu > 60 or ram > 70 or disk > 75 or (temp is not None and temp > 65):
        return discord.Color.yellow()
    return discord.Color.green()


def build_status_embed(stats: dict) -> discord.Embed:
    cpu = stats["cpu"]
    ram = stats["ram"]
    disk = stats["disk"]
    temp = stats["temperature"]
    load = stats["load"]

    embed = discord.Embed(
        title="🖥️ Server Status Dashboard",
        color=_status_color(cpu, ram["percent"], disk["percent"], temp),
        timestamp=datetime.utcnow(),
    )

    embed.add_field(
        name="⚡ CPU Usage",
        value=f"`{_progress_bar(cpu)}` **{cpu:.1f}%**",
        inline=False,
    )
    embed.add_field(
        name="🧠 RAM",
        value=f"`{_progress_bar(ram['percent'])}` **{ram['used_gb']:.1f} / {ram['total_gb']:.1f} GB** ({ram['percent']:.1f}%)",
        inline=False,
    )
    embed.add_field(
        name="💾 Disk",
        value=f"`{_progress_bar(disk['percent'])}` **{disk['used_gb']:.1f} / {disk['total_gb']:.1f} GB** ({disk['percent']:.1f}%)",
        inline=False,
    )

    temp_str = f"{temp:.1f}°C" if temp is not None else "N/A"
    temp_icon = "🔥" if temp is not None and temp > 75 else "🌡️"
    embed.add_field(name=f"{temp_icon} CPU Temp", value=temp_str, inline=True)
    embed.add_field(
        name="📊 Load Avg",
        value=f"{load[0]:.2f} / {load[1]:.2f} / {load[2]:.2f}",
        inline=True,
    )
    embed.add_field(name="⏱️ Uptime", value=stats["uptime"], inline=True)
    embed.add_field(name="🔄 Processes", value=str(stats["processes"]), inline=True)

    users = stats["users"]
    embed.add_field(
        name="👤 Logged-in Users",
        value=", ".join(users) if users else "None",
        inline=True,
    )

    embed.set_footer(text="Updates every 30 seconds")
    return embed


class Dashboard(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._update_loop.start()

    def cog_unload(self) -> None:
        self._update_loop.cancel()

    @tasks.loop(seconds=30)
    async def _update_loop(self) -> None:
        channel = self.bot.get_channel(STATUS_CHANNEL_ID)
        if channel is None:
            return

        embed = build_status_embed(get_all_stats())
        msg_id = get_message_id("status_message")

        if msg_id:
            try:
                msg = await channel.fetch_message(msg_id)
                await msg.edit(embed=embed)
                return
            except discord.NotFound:
                pass
            except discord.HTTPException as e:
                print(f"[dashboard] Edit failed (will retry): {e}")
                return

        msg = await channel.send(embed=embed)
        set_message_id("status_message", msg.id)

    @_update_loop.before_loop
    async def _before(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Dashboard(bot))
