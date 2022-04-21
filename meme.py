import json
import logging
from random import SystemRandom

import asyncpraw
import discord
import requests
from discord.commands import slash_command
from discord.ext import commands

# Start logger and load configs
logging.basicConfig(level=logging.INFO)
f = open('data/config.json', 'r+')
config = json.load(f)
f.close()

# Create random object
srandom = SystemRandom()

# Create reddit client
reddit = asyncpraw.Reddit(client_id=config['reddit'],
                          client_secret=config['redditsecret'],
                          user_agent="u/sharpaxeyt")


class Meme(commands.Cog):
    def __init__(self, client):
        """
        Creates a meme cog

        Parameter
        ---------
        client :
            bot client
        """
        self.client = client
        self._last_member = None

    @slash_command(name='meme', description="Sends a meme from r/izlam")
    async def meme(self, ctx):
        async with ctx.channel.typing():

            subs = ['izlam', 'MemriTVmemes']
            discord_subreddit = srandom.choice(subs)
            try:
                subreddit = await reddit.subreddit(discord_subreddit)
                posts = [post async for post in subreddit.hot(limit=20)]
                random_post_number = srandom.choice(range(0, 20))
                submission = posts[random_post_number]
                if not submission.stickied:
                    discordreceive = {'title': submission.title,
                                      'link': f'https://www.reddit.com{submission.permalink}'}

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
                    await ctx.respond(embed=embed)
            except Exception:
                await ctx.respond('There was an error. Please try again.')
