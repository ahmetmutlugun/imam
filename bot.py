import json
import logging
from random import SystemRandom
import discord
from discord.ext import commands
from cogs.meme import Meme
from cogs.quran_audio import Recite
from cogs.dua import Dua
from cogs.prayer import PrayerTimes
from cogs.trivia import Trivia


# Load logger, configs, and random object
logging.basicConfig(level=logging.INFO)
f = open('data/config.json', 'r+')
config = json.load(f)
f.close()

prefix = "imam "

client = commands.AutoShardedBot(description="A Discord bot with a set of Islamic tools.")

guilds = []
guild_ids = []
srandom = SystemRandom()


# Case insensitivity can cause performance issues
@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(prefix + "help"))
    print("Bot Ready")
    for guild in client.guilds:
        guilds.append(guild)
        guild_ids.append(guild.id)
    print(guilds)


@commands.Cog.listener()
async def on_member_join(member):
    channel = member.guild.system_channel
    if channel is not None:
        await channel.respond('As-salamu alaykum {0.mention}.'.format(member))


@client.slash_command(name='welcome', description="Welcome a user")
async def welcome(self, ctx, *, member: discord.Member = None):
    member = member or ctx.author
    if self._last_member is None or self._last_member.id != member.id:
        await ctx.respond(f'As-salamu alaykum {member.mention}')
    else:
        await ctx.respond(f'As-salamu alaykum {member.mention}')
    self._last_member = member


@client.slash_command(name='ping', description="Displays ping")
async def _ping(ctx):  # Defines a new "context" (ctx) command called "ping."
    await ctx.respond(f"Pong! ({round(client.latency * 1000)}ms)")

@client.slash_command(name='pp', description="Sends the profile picture of a user.")
async def pp(ctx, member: discord.Member = None):
    if member is None:
        embed = discord.Embed(title="Here is your profile picture:", type='rich', color=0x048c28)
        embed.set_image(url=ctx.author.avatar_url)
        embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                                  "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")
        await ctx.respond(embed=embed)
    else:
        embed = discord.Embed(title="Here is the profile picture of " + member.display_name + ":", type='rich',
                              color=0x048c28)
        embed.set_image(url=member.avatar_url)
        embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                                  "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")
        await ctx.respond(embed=embed)


@client.slash_command(name='changelog', description="Shows the latest changes.")
async def changelog(ctx):
    embed = discord.Embed(title="Changelog", type='rich', color=0x048c28)
    changelogs = open("data/changelog.txt", "r")
    embed.add_field(name="Latest Changes:", value=changelogs.read())
    embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                              "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")
    await ctx.respond(embed=embed)
    changelogs.close()


client.add_cog(Dua(client, config))
client.add_cog(PrayerTimes(client, config))
client.add_cog(Recite(client))
client.add_cog(Meme(client, config))
client.add_cog(Trivia(client))
client.run(config['discord'])
