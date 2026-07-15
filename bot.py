import logging
import logging.handlers
import os

import discord
from discord import Status
from discord.ext import commands
from dotenv import load_dotenv

from cogs.dua import Dua
from cogs.date import Date
from cogs.prayer import PrayerTimes
from cogs.stats import Stats
from cogs.trivia import Trivia
from cogs.quran_audio import Recite
from cogs.quran_pages import Quran_Pages

load_dotenv()

# Console for docker logs, plus a rotating file (survives container recreation
# via the ./logs bind mount in docker-compose.yml)
_log_dir = os.environ.get('LOG_DIR', 'logs')
os.makedirs(_log_dir, exist_ok=True)
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO').upper(),
    format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            os.path.join(_log_dir, 'imam.log'),
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8',
        ),
    ],
)

config = {
    'discord':       os.environ['DISCORD_TOKEN'],
    'sunnah':        os.environ['SUNNAH_API_KEY'],
    'positionstack': os.environ['POSITIONSTACK_API_KEY'],
    'encrypt_key':   os.environ['ENCRYPT_KEY'],
}


def set_author_imam(embed: discord.Embed):
    embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                              "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")


class ImamBot(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.voice_states = True
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            description="A Discord bot with a set of Islamic tools.",
            status=Status.online,
            activity=discord.Game("/help"),
        )

    async def setup_hook(self):
        await self.add_cog(Dua(self, config))
        await self.add_cog(Date(self, config))
        await self.add_cog(PrayerTimes(self, config))
        await self.add_cog(Recite(self))
        await self.add_cog(Quran_Pages(self))
        await self.add_cog(Trivia(self))
        await self.add_cog(Stats(self))
        await self.tree.sync()


client = ImamBot()


@client.event
async def on_ready():
    logging.info("Bot Ready")
    guilds = [guild async for guild in client.fetch_guilds(limit=10000)]
    logging.info(f"Server count: {len(guilds)}")


@client.tree.command(name='ping', description="Displays ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! ({round(client.latency * 1000)}ms)")


@client.tree.command(name='help', description="Shows the latest changes.")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="List of /commands", type='rich', color=0x048c28)
    embed.add_field(name="General:", value="ping, help, about, stats")
    embed.add_field(name="Dua:", value="hadith, basmalah, pray, salawat, esma, takbeer, dhikr, salaam")
    embed.add_field(name="Prayer:", value="location, prayer, prayer_now")
    embed.add_field(name="Quran:", value="quran")
    embed.add_field(name="Trivia:", value="trivia")
    embed.add_field(name="Date", value="hijri")
    set_author_imam(embed)
    await interaction.response.send_message(embed=embed)


@client.tree.command(name="about", description="About the bot and the developers")
async def about(interaction: discord.Interaction):
    embed = discord.Embed(title="About Us", type='rich', color=0x048c28)
    embed.add_field(name="Thanks for using Imam!",
                    value="ImamBot was created as a project by two students. You can find more about the project "
                          "at https://github.com/ahmetmutlugun/imam. If you want to support the project, "
                          "your feedback is more valuable than anything else. You can contact us at imam@etka.io "
                          "or leave an issue on GitHub.")
    set_author_imam(embed)
    await interaction.response.send_message(embed=embed)


# log_handler=None: logging is already configured above; discord.py would
# otherwise install a second handler and every line would print twice
client.run(config['discord'], log_handler=None)
