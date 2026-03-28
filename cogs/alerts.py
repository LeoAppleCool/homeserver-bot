"""Alert monitoring — system thresholds and Docker container state changes."""

import os
from datetime import datetime

import discord
from discord.ext import commands, tasks

from utils.docker_utils import get_containers
from utils.system_stats import get_all_stats

ALERTS_CHANNEL_ID = int(os.getenv("ALERTS_CHANNEL_ID", "0"))
DOCKER_ALERTS_CHANNEL_ID = int(os.getenv("DOCKER_ALERTS_CHANNEL_ID", "0"))

CPU_THRESHOLD = 80.0
RAM_THRESHOLD = 85.0
DISK_THRESHOLD = 90.0
TEMP_THRESHOLD = 75.0


class Alerts(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Keys of currently active system alerts
        self._active: set[str] = set()
        # name -> container dict from last poll
        self._container_states: dict[str, dict] = {}
        self._check_system.start()
        self._check_docker.start()

    def cog_unload(self) -> None:
        self._check_system.cancel()
        self._check_docker.cancel()

    # ------------------------------------------------------------------
    # System resource alerts
    # ------------------------------------------------------------------

    @tasks.loop(seconds=30)
    async def _check_system(self) -> None:
        channel = self.bot.get_channel(ALERTS_CHANNEL_ID)
        if channel is None:
            return

        stats = get_all_stats()
        cpu = stats["cpu"]
        ram = stats["ram"]["percent"]
        disk = stats["disk"]["percent"]
        temp = stats["temperature"]

        await self._threshold(
            channel, "cpu", cpu > CPU_THRESHOLD,
            f"🔥 **CPU Alert** — Usage at **{cpu:.1f}%** (limit: {CPU_THRESHOLD:.0f}%)",
            f"✅ **CPU Resolved** — Usage back to **{cpu:.1f}%**",
        )
        await self._threshold(
            channel, "ram", ram > RAM_THRESHOLD,
            f"🧠 **RAM Alert** — Usage at **{ram:.1f}%** "
            f"({stats['ram']['used_gb']:.1f}/{stats['ram']['total_gb']:.1f} GB, limit: {RAM_THRESHOLD:.0f}%)",
            f"✅ **RAM Resolved** — Usage back to **{ram:.1f}%**",
        )
        await self._threshold(
            channel, "disk", disk > DISK_THRESHOLD,
            f"💾 **Disk Alert** — Usage at **{disk:.1f}%** "
            f"({stats['disk']['used_gb']:.1f}/{stats['disk']['total_gb']:.1f} GB, limit: {DISK_THRESHOLD:.0f}%)",
            f"✅ **Disk Resolved** — Usage back to **{disk:.1f}%**",
        )
        if temp is not None:
            await self._threshold(
                channel, "temp", temp > TEMP_THRESHOLD,
                f"🌡️ **Temperature Alert** — CPU at **{temp:.1f}°C** (limit: {TEMP_THRESHOLD:.0f}°C)",
                f"✅ **Temperature Resolved** — CPU back to **{temp:.1f}°C**",
            )

    async def _threshold(
        self,
        channel: discord.TextChannel,
        key: str,
        triggered: bool,
        alert_text: str,
        resolve_text: str,
    ) -> None:
        if triggered and key not in self._active:
            self._active.add(key)
            embed = discord.Embed(description=alert_text, color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text="System Alert")
            await channel.send(embed=embed)
        elif not triggered and key in self._active:
            self._active.discard(key)
            embed = discord.Embed(description=resolve_text, color=discord.Color.green(), timestamp=datetime.utcnow())
            embed.set_footer(text="Alert Resolved")
            await channel.send(embed=embed)

    # ------------------------------------------------------------------
    # Docker container alerts
    # ------------------------------------------------------------------

    @tasks.loop(seconds=30)
    async def _check_docker(self) -> None:
        channel = self.bot.get_channel(DOCKER_ALERTS_CHANNEL_ID)
        if channel is None:
            return

        current = {c["name"]: c for c in get_containers()}

        for name, container in current.items():
            prev = self._container_states.get(name)

            if prev is None:
                # First time seeing this container — just record, no alert
                self._container_states[name] = container
                continue

            if prev["running"] and not container["running"]:
                embed = discord.Embed(
                    title="❌ Container Down",
                    description=f"**{name}** has stopped.",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow(),
                )
                embed.add_field(name="Status", value=container["status"], inline=True)
                embed.add_field(name="Image", value=f"`{container['image']}`", inline=True)
                embed.set_footer(text="Docker Alert")
                await channel.send(embed=embed)

            elif not prev["running"] and container["running"]:
                embed = discord.Embed(
                    title="✅ Container Recovered",
                    description=f"**{name}** is running again.",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow(),
                )
                embed.add_field(name="Uptime", value=container["uptime"], inline=True)
                embed.set_footer(text="Docker Alert")
                await channel.send(embed=embed)

            elif container["running"] and container["restart_count"] > prev["restart_count"]:
                embed = discord.Embed(
                    title="🔁 Container Restarted",
                    description=f"**{name}** restarted unexpectedly.",
                    color=discord.Color.yellow(),
                    timestamp=datetime.utcnow(),
                )
                embed.add_field(name="Total Restarts", value=str(container["restart_count"]), inline=True)
                embed.add_field(name="Image", value=f"`{container['image']}`", inline=True)
                embed.set_footer(text="Docker Alert")
                await channel.send(embed=embed)

            self._container_states[name] = container

        # Remove stale entries for containers that no longer exist
        for name in list(self._container_states):
            if name not in current:
                del self._container_states[name]

    @_check_system.before_loop
    @_check_docker.before_loop
    async def _before(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Alerts(bot))
