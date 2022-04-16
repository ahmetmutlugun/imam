import asyncio
import time
import json
import random
import discord
import praw
import requests
import logging
from discord_slash import SlashCommand
from discord_slash.utils.manage_components import create_button, create_actionrow, wait_for_component

from dua import Prayer
from quran_audio import Recite
from webscrape_and_data import Webscraping2, create_user, set_user_data

from discord.ext import commands
from discord.ext.commands import Bot
from discord_components import ButtonStyle
from discord_slash.model import ButtonStyle

logging.basicConfig(level=logging.INFO)
f = open('data/config.json', 'r+')
config = json.load(f)
f.close()

prefix = "imam "

reddit = praw.Reddit(client_id=config['reddit'],
                     client_secret=config['redditsecret'],
                     user_agent="u/sharpaxeyt")

client: Bot = commands.Bot(command_prefix=[prefix, 'Imam '], case_insensitive=True, description="A bot for islamic "
                                                                                                "commands and tools.")
slash = SlashCommand(client, sync_commands=True)  # Declares slash commands through the client.

guilds = []
guild_ids = []


# Case insensitivity can cause performance issues

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(prefix + "help"))
    print("Bot Ready")
    for guild in client.guilds:
        guilds.append(guild)
        guild_ids.append(guild.id)


@commands.Cog.listener()
async def on_member_join(member):
    channel = member.guild.system_channel
    if channel is not None:
        await channel.send('As-salamu alaykum {0.mention}.'.format(member))


@commands.command(brief='Welcome a user.', aliases=['wb'])
async def welcome(self, ctx, *, member: discord.Member = None):
    member = member or ctx.author
    if self._last_member is None or self._last_member.id != member.id:
        await ctx.send(f'As-salamu alaykum {member.mention}')
    else:
        await ctx.send(f'As-salamu alaykum {member.mention}')
    self._last_member = member


@client.command(brief='Displays bot ping')
async def ping(ctx):
    await ctx.send(f"My ping is: {round(client.latency * 1000)}ms")


@slash.slash(name="ping", guild_ids=guild_ids)
async def _ping(ctx):  # Defines a new "context" (ctx) command called "ping."
    await ctx.send(f"Pong! ({client.latency * 1000}ms)")


@client.command(brief="Takbeer", aliases=['tekbir', 'takbir'])
async def takbeer(ctx):
    await ctx.send("Allahuakbar")


@client.command(brief="Sends a reminder", aliases=['zikr'])
async def dhikr(ctx):
    await ctx.send(
        "Indeed, it is We (Allah) who created humankind and fully know what their souls whisper to them, and We are closer to "
        "them than their jugular vein (By His knowledge). (Qaf , ayah 16)")


@client.command(aliases=['islammeme', 'memritv', 'meme'])
async def izlam(ctx):
    async with ctx.channel.typing():
        subs = ['izlam', 'MemriTVmemes']
        discordsubreddit = random.choice(subs)
        try:
            subreddit = reddit.subreddit(discordsubreddit)
            posts = [post for post in subreddit.hot(limit=20)]
            random_post_number = random.randint(0, 20)
            submission = posts[random_post_number]
            if not submission.stickied:
                discordreceive = {'title': submission.title, 'link': f'https://www.reddit.com{submission.permalink}'}

                r = requests.get(
                    discordreceive['link'] + '.json',
                    headers={
                        'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, '
                                      'like Gecko) Chrome/85.0.4183.102 Safari/537.36'})

                data = r.json()
                image_url = str(data[0]['data']['children'][0]['data']['url_overridden_by_dest'])
                embed = discord.Embed(title=discordreceive['title'], url=discordreceive['link'])
                embed.set_image(url=str(image_url))
                embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                                          "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")
                await ctx.send(embed=embed)
        except Exception:
            await ctx.send('There was an error. Please try again.')


@client.command(brief='Send a greeting message.',
                aliases=['sa', 'assalamualaikum', 'selamunaleykum', 'selam', 'As-salamu alaykum', 'as salamu alaykum'])
async def slm(ctx):
    responses = [' wa ʿalaykumu s-salām']
    await ctx.send(f'{random.choice(responses)}')


@client.command(brief='Sends the profile picture of a user', aliases=["profile", "profilepicture"])
async def pp(ctx, member: discord.Member = None):
    if member is None:
        embed = discord.Embed(title="Here is your profile picture:", type='rich', color=0x048c28)
        embed.set_image(url=ctx.author.avatar_url)
        embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                                  "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Here is the profile picture of " + member.display_name + ":", type='rich',
                              color=0x048c28)
        embed.set_image(url=member.avatar_url)
        embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                                  "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")
        await ctx.send(embed=embed)


@client.command(brief='', aliases=['patch', 'patch_notes', 'log'])
async def changelog(ctx):
    embed = discord.Embed(title="Changelog", type='rich', color=0x048c28)
    changelogs = open("data/changelog.txt", "r")
    embed.add_field(name="Latest Changes:", value=changelogs.read())
    embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                              "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")
    await ctx.send(embed=embed)
    changelogs.close()


@client.command(brief='Asks a random islamic trivia question', aliases=['quiz', 'test', 'question'])
async def trivia(ctx):
    author_id = str(ctx.author)
    trivia_embed = create_trivia_embed(author_id)

    action_row = create_actionrow(*trivia_embed[1])
    await ctx.send(embed=trivia_embed[0], components=[action_row])
    while True:
        try:
            button_ctx = await wait_for_component(client, components=action_row,
                                                  timeout=600)
            if button_ctx.custom_id == trivia_embed[2]:
                await ctx.send("That is the correct answer!", delete_after=3)

                for _ in range(0, 10):
                    trivia_embed[0].remove_field(0)
                trivia_embed[0].add_field(name="__Questions__", value=trivia_embed[4])
                trivia_embed[0].add_field(name="Correct answer:", value=trivia_embed[3])
                await button_ctx.edit_origin(embed=trivia_embed[0], components=None)
                return
            else:
                await ctx.send("That is the wrong answer! Please try again!", delete_after=3)
                await button_ctx.edit_origin(embed=trivia_embed[0])

        except asyncio.TimeoutError:
            break


def get_random_question():
    """
    Selects a random question from the questions json file
    """
    with open('data/questions.json', 'r+') as f:
        data = json.load(f)
    return data[str(random.randint(0, len(data) - 1))]


def create_trivia_embed(author_id):
    """
    Creates the trivia embed of a question
    """
    data = get_random_question()
    embed = discord.Embed(title='Islamic Trivia', type='rich', color=discord.Color.blue(),
                          description="Pick the answer choice that corresponds with the best answer.", )
    embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                              "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")
    embed.set_thumbnail(
        url="https://media.discordapp.net/attachments/453076515777937428/852697275716599808/IMAM-BOT-PSD.png?width"
            "=676&height=676")

    # Add question field 
    embed.add_field(name="__Question__", value=data["question"], inline=False)
    # Add order of options randomly
    aliases = ["A", "B", "C", "D"]
    options = ["a", "b", "c", "d"]
    for al in aliases:
        random.shuffle(options, time.time())
        embed.add_field(f"*Option {al}", value=data[options.pop()], inline=False)

    r = str(random.randint(1, 1000))
    buttons = [

        create_button(style=ButtonStyle.blurple, label="A",
                      custom_id=author_id + "a" + r),
        create_button(style=ButtonStyle.blurple, label="B",
                      custom_id=author_id + "b" + r),
        create_button(style=ButtonStyle.blurple, label="C",
                      custom_id=author_id + "c" + r),
        create_button(style=ButtonStyle.blurple, label="D",
                      custom_id=author_id + "d" + r)
    ]
    print(author_id + data["correct_answer"] + r)

    return embed, buttons, author_id + data["correct_answer"] + r, data[data["correct_answer"]], data["question"]


client.add_cog(Prayer(client))
client.add_cog(Webscraping2(client))
client.add_cog(Recite(client))
client.run(config['discord'])
