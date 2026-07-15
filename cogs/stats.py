import logging
import os
import time
from datetime import date

import discord
import redis
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)

_redis = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=6379, decode_responses=True)

# Daily counters are kept for 90 days; all-time counters never expire
_DAILY_TTL = 90 * 24 * 3600


def _today() -> str:
    return date.today().isoformat()


class Stats(commands.Cog):
    """Logs every slash command invocation and records usage counters in Redis."""

    def __init__(self, client):
        self.client = client
        self.started_at = time.time()
        client.tree.on_error = self.on_app_command_error

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction,
                                        command: app_commands.Command):
        name = command.qualified_name
        logger.info(f"/{name} by user {interaction.user.id} in guild {interaction.guild_id or 'DM'}")
        try:
            today = _today()
            pipe = _redis.pipeline()
            pipe.hincrby("stats:commands", name, 1)
            pipe.hincrby(f"stats:commands:{today}", name, 1)
            pipe.expire(f"stats:commands:{today}", _DAILY_TTL)
            pipe.pfadd("stats:users", interaction.user.id)
            pipe.pfadd(f"stats:users:{today}", interaction.user.id)
            pipe.expire(f"stats:users:{today}", _DAILY_TTL)
            if interaction.guild_id:
                pipe.pfadd("stats:guilds", interaction.guild_id)
            pipe.execute()
        except redis.RedisError as e:
            logger.warning(f"Failed to record usage stats: {e}")

    async def on_app_command_error(self, interaction: discord.Interaction,
                                   error: app_commands.AppCommandError):
        name = interaction.command.qualified_name if interaction.command else "unknown"
        logger.error(f"/{name} failed for user {interaction.user.id} in guild "
                     f"{interaction.guild_id or 'DM'}: {error}", exc_info=error)
        try:
            _redis.hincrby("stats:errors", name, 1)
        except redis.RedisError:
            pass
        message = "Something went wrong running that command. Please try again."
        try:
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
        except discord.HTTPException:
            pass

    @app_commands.command(name='stats', description="Bot usage statistics")
    async def stats(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Bot Stats", type='rich', color=0x048c28)
        embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                                  "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")

        uptime = int(time.time() - self.started_at)
        days, rem = divmod(uptime, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, _ = divmod(rem, 60)
        embed.add_field(name="Uptime", value=f"{days}d {hours}h {minutes}m")
        embed.add_field(name="Servers", value=str(len(self.client.guilds)))
        embed.add_field(name="Latency", value=f"{round(self.client.latency * 1000)}ms")

        try:
            all_time = _redis.hgetall("stats:commands")
            today = _redis.hgetall(f"stats:commands:{_today()}")
            users_today = _redis.pfcount(f"stats:users:{_today()}")
        except redis.RedisError as e:
            logger.warning(f"Failed to read usage stats: {e}")
            all_time, today, users_today = {}, {}, 0

        if all_time:
            top = sorted(all_time.items(), key=lambda kv: int(kv[1]), reverse=True)[:10]
            embed.add_field(name="Top commands (all time)",
                            value="\n".join(f"/{name}: {count}" for name, count in top),
                            inline=False)
        embed.add_field(name="Commands today", value=str(sum(int(c) for c in today.values())))
        embed.add_field(name="Unique users today", value=str(users_today))

        await interaction.response.send_message(embed=embed)
