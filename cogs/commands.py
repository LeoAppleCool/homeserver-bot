"""Slash commands: /status /containers /logs /restart /uptime"""

import os
from datetime import datetime

import discord
import psutil
from discord import app_commands
from discord.ext import commands

from cogs.dashboard import build_status_embed
from cogs.docker_monitor import build_docker_embed
from utils.docker_utils import get_container_logs, get_containers, restart_container
from utils.system_stats import get_all_stats, get_uptime

GUILD_ID = int(os.getenv("GUILD_ID", "0"))


class Commands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------
    # /status
    # ------------------------------------------------------------------

    @app_commands.command(name="status", description="Show full server stats on demand")
    async def status(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        embed = build_status_embed(get_all_stats())
        await interaction.followup.send(embed=embed)

    # ------------------------------------------------------------------
    # /containers
    # ------------------------------------------------------------------

    @app_commands.command(name="containers", description="List all Docker containers with status")
    async def containers(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        embed = build_docker_embed(get_containers())
        await interaction.followup.send(embed=embed)

    # ------------------------------------------------------------------
    # /logs
    # ------------------------------------------------------------------

    @app_commands.command(name="logs", description="Show last N lines of a container's logs")
    @app_commands.describe(
        container_name="Name of the Docker container",
        lines="Number of log lines to show (1–200, default 50)",
    )
    async def logs(
        self,
        interaction: discord.Interaction,
        container_name: str,
        lines: int = 50,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        lines = max(1, min(lines, 200))
        output = get_container_logs(container_name, lines)

        # Discord embed description limit is 4096 chars; code block overhead = 8
        max_chars = 4000
        if len(output) > max_chars:
            output = "…(truncated)\n" + output[-max_chars:]

        embed = discord.Embed(
            title=f"📋 Logs — {container_name}",
            description=f"```\n{output}\n```",
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"Last {lines} line(s)")
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # /restart  (admin only)
    # ------------------------------------------------------------------

    @app_commands.command(name="restart", description="Restart a Docker container (admin only)")
    @app_commands.describe(container_name="Name of the Docker container to restart")
    @app_commands.checks.has_permissions(administrator=True)
    async def restart(self, interaction: discord.Interaction, container_name: str) -> None:
        await interaction.response.defer(ephemeral=True)
        success, message = restart_container(container_name)
        embed = discord.Embed(
            title="✅ Restart" if success else "❌ Restart Failed",
            description=message,
            color=discord.Color.green() if success else discord.Color.red(),
            timestamp=datetime.utcnow(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @restart.error
    async def restart_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You need **Administrator** permission to restart containers.", ephemeral=True
            )

    # ------------------------------------------------------------------
    # /uptime
    # ------------------------------------------------------------------

    @app_commands.command(name="uptime", description="Show system uptime")
    async def uptime(self, interaction: discord.Interaction) -> None:
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        embed = discord.Embed(title="⏱️ System Uptime", color=discord.Color.blue(), timestamp=datetime.utcnow())
        embed.add_field(name="Uptime", value=get_uptime(), inline=False)
        embed.add_field(name="Boot Time", value=boot_time.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Commands(bot))
