import json
import logging
from random import SystemRandom
import discord
from discord import Status
from discord.ext import commands

from cogs.dua import Dua
from cogs.prayer import PrayerTimes, auto_delete_users
from cogs.trivia import Trivia
from cogs.quran_audio import Recite
from cogs.quran_pages import Quran_Pages
from cogs.meme import Meme

# TODO: Test set_author_imam and use it in other embeds

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


@commands.Cog.listener()
async def on_member_join(member):
    channel = member.guild.system_channel
    if channel is not None:
        await channel.respond('As-salamu alaykum {0.mention}.'.format(member))


@client.slash_command(name='welcome', description="Welcome a user")
async def welcome(ctx, member: discord.Member):
    await ctx.respond(f'As-salamu alaykum {member.mention}')


@client.slash_command(name='ping', description="Displays ping")
async def _ping(ctx):  # Defines a new "context" (ctx) command called "ping."
    await ctx.respond(f"Pong! ({round(client.latency * 1000)}ms)")


@client.slash_command(name='pp', description="Sends the profile picture of a user.")
async def pp(ctx, member: discord.Member = None):
    embed = None

    if member is None:
        embed = discord.Embed(title="Here is your profile picture:", type='rich', color=0x048c28)
        embed.set_image(url=ctx.author.avatar)

        await ctx.respond(embed=embed)
    else:
        embed = discord.Embed(title="Here is the profile picture of " + member.display_name + ":", type='rich',
                              color=0x048c28)
        embed.set_image(url=member.avatar)

    set_author_imam(embed)
    await ctx.respond(embed=embed)


@client.slash_command(name='changelog', description="Shows the latest changes.")
async def changelog(ctx):
    embed = discord.Embed(title="Changelog", type='rich', color=0x048c28)
    changelogs = open("cogs/data/changelog.txt", "r")
    embed.add_field(name="Latest Changes:", value=changelogs.read())
    set_author_imam(embed)
    await ctx.respond(embed=embed)
    changelogs.close()


@client.slash_command(name='help', description="Shows the latest changes.")
async def help(ctx):
    embed = discord.Embed(title="List of /commands", type='rich', color=0x048c28)
    embed.add_field(name="Main:", value="ping, changelog, pp, welcome, help")
    embed.add_field(name="Dua:", value="hadith, basmalah, pray, salawat, esma, takbeer, dhikr, salaam")
    embed.add_field(name="Meme:", value="meme")
    embed.add_field(name="Prayer:", value="location, prayer, prayer_now")
    embed.add_field(name="Quran:", value="quran")
    embed.add_field(name="Trivia:", value="trivia")
    set_author_imam(embed)
    await ctx.respond(embed=embed)


def set_author_imam(embed: discord.Embed):
    embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                              "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")


client.add_cog(Dua(client, config))
client.add_cog(PrayerTimes(client, config))
client.add_cog(Recite(client))
client.add_cog(Quran_Pages(client))
client.add_cog(Meme(client, config))
client.add_cog(Trivia(client))
client.run(config['discord'])
