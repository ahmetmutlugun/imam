import logging
import os

import discord
from discord import Status
from discord.ext import commands
from dotenv import load_dotenv

from cogs.dua import Dua
from cogs.date import Date
from cogs.prayer import PrayerTimes
from cogs.trivia import Trivia
from cogs.quran_audio import Recite
from cogs.quran_pages import Quran_Pages

load_dotenv()
logging.basicConfig(level=logging.INFO)

config = {
    'discord':       os.environ['DISCORD_TOKEN'],
    'sunnah':        os.environ['SUNNAH_API_KEY'],
    'positionstack': os.environ['POSITIONSTACK_API_KEY'],
    'encrypt_key':   os.environ['ENCRYPT_KEY'],
}

client = commands.AutoShardedBot(description="A Discord bot with a set of Islamic tools.", status=Status.online,
                                 activity=discord.Game("/help"))


# Case insensitivity can cause performance issues
@client.event
async def on_ready():
    logging.info("Bot Ready")
    guilds = [guild async for guild in client.fetch_guilds(limit=10000)]
    logging.info(f"Server count: {len(guilds)}")
    # await set_all_quran_editions()



@client.slash_command(name='ping', description="Displays ping")
async def ping(ctx):
    await ctx.respond(f"Pong! ({round(client.latency * 1000)}ms)")


@client.slash_command(name='help', description="Shows the latest changes.")
async def help(ctx):
    embed = discord.Embed(title="List of /commands", type='rich', color=0x048c28)
    embed.add_field(name="General:", value="ping, help, about")
    embed.add_field(name="Dua:", value="hadith, basmalah, pray, salawat, esma, takbeer, dhikr, salaam")
    embed.add_field(name="Prayer:", value="location, prayer, prayer_now")
    embed.add_field(name="Quran:", value="quran")
    embed.add_field(name="Trivia:", value="trivia")
    embed.add_field(name="Date", value="hijri")
    set_author_imam(embed)
    await ctx.respond(embed=embed)


@client.slash_command(name = "about", description = "About the bot and the developers")
async def about(ctx):
    embed = discord.Embed(title="About Us", type='rich', color=0x048c28)
    embed.add_field(name="Thanks for using Imam!",
                    value="ImamBot was created as a project by two students. You can find more about the project "
                          "at https://github.com/ahmetmutlugun/imam. If you want to support the project, "
                          "your feedback is more valuable than anything else. You can contact us at imam@etka.io "
                          "or leave an issue on GitHub.")
    set_author_imam(embed)
    await ctx.respond(embed=embed)


def set_author_imam(embed: discord.Embed):
    embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                              "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")


client.add_cog(Dua(client, config))
client.add_cog(Date(client, config))
client.add_cog(PrayerTimes(client, config))
client.add_cog(Recite(client))
client.add_cog(Quran_Pages(client))
client.add_cog(Trivia(client))
client.run(config['discord'])
