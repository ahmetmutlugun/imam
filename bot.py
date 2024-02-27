import json
import logging
from random import SystemRandom
import discord
from discord import Status
from discord.ext import commands

from cogs.dua import Dua
from cogs.date import Date
from cogs.prayer import PrayerTimes, auto_delete_users
# from cogs.quran_cache import set_all_quran_editions
from cogs.trivia import Trivia
from cogs.quran_audio import Recite
from cogs.quran_pages import Quran_Pages
from cogs.meme import Meme

# Load logger, configs, and  random object
logging.basicConfig(level=logging.DEBUG)
f = open('cogs/data/config.json', 'r+')
config = json.load(f)
f.close()

prefix = "imam "

client = commands.AutoShardedBot(description="A Discord bot with a set of Islamic tools.", status=Status.online,
                                 activity=discord.Game("/help"))
system_random = SystemRandom()


# Case insensitivity can cause performance issues
@client.event
async def on_ready():
    auto_delete_users()
    logging.info("Bot Ready")
    guilds = await client.fetch_guilds(limit=10000).flatten()
    logging.info(f"Server count: {len(guilds)}")
    # await set_all_quran_editions()


@commands.Cog.listener()
async def on_member_join(member):
    channel = member.guild.system_channel
    if channel is not None:
        await channel.respond('As-salamu alaykum {0.mention}.'.format(member))


@client.slash_command(name='ping', description="Displays ping")
async def ping(ctx):
    await ctx.respond(f"Pong! ({round(client.latency * 1000)}ms)")


@client.slash_command(name='help', description="Shows the latest changes.")
async def help(ctx):
    embed = discord.Embed(title="List of /commands", type='rich', color=0x048c28)
    embed.add_field(name="General:", value="ping, profile, help, about")
    embed.add_field(name="Dua:", value="hadith, basmalah, pray, salawat, esma, takbeer, dhikr, salaam")
    embed.add_field(name="Meme:", value="meme")
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
client.add_cog(Meme(client, config))
client.add_cog(Trivia(client))
client.run(config['discord'])
