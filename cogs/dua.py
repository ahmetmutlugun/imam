import asyncio
import json
import os
import time
import textwrap
import logging
import re

import aiohttp

from random import SystemRandom

import discord
from discord import app_commands
from discord.ext import commands

from cogs.paginator import EmbedPaginator

system_random = SystemRandom()

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

collection_names = [
    'ahmad',
    'bukhari',
    'muslim',
    'tirmidhi',
    'abudawud',
    'nasai',
    'ibnmajah',
    'malik',
    'riyadussalihin',
    'adab',
    'bulugh',
    'shamail',
    'mishkat',
    'qudsi40',
    'nawawi40',
    'hisn',
]

collections_str = "ahmad, bukhari, muslim, tirmidhi, abudawud, nasai, ibnmajah, malik, riyadussalihin, adab, " \
                  "bulugh, shamail, mishkat, qudsi40, nawawi40, hisn "


def process_hadith(hadith_json):
    final_hadith = hadith_json['hadith'][0]['body']
    html_tags = re.compile(r'<[^>]+>')
    return html_tags.sub('', final_hadith).replace('`', '')


def create_hadith_embed(number: int, collection: str, hadith: str, page: int, grade: str) -> discord.Embed:
    embed = discord.Embed(title=f"Hadith {number} from {collection} collection.", type='rich',
                          color=0x048c28)
    embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                              "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")
    embed.add_field(name=f"{collection} {number}  Page {page}", value=hadith)
    embed.add_field(name="Grade", value=grade or "N/A")
    return embed


class Dua(commands.Cog):
    def __init__(self, client, config):
        self.client = client
        self.config = config

    @app_commands.command(name='hadith', description="Sends a hadith. Pick a collection, or leave everything blank for a random one.")
    @app_commands.describe(
        collection="Hadith collection (leave blank for fully random)",
        number="Specific hadith number (leave blank for a random one from the collection)"
    )
    @app_commands.choices(collection=[app_commands.Choice(name=c, value=c) for c in collection_names])
    async def hadith(self, interaction: discord.Interaction, collection: str = "random", number: int = None):
        if collection.lower() not in collection_names and collection != "random":
            await interaction.response.send_message(
                f"Your collection is not supported. Please choose from the following collections: \n {collections_str}")
            return

        await interaction.response.defer()

        if collection == "random":
            url = "https://api.sunnah.com/v1/hadiths/random"
        elif number is None:
            # Fetch collection metadata to get total hadith count, then pick a random one
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"https://api.sunnah.com/v1/collections/{collection}",
                        headers={"X-API-Key": self.config['sunnah']},
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as r:
                        r.raise_for_status()
                        meta = await r.json()
                total = meta.get("totalHadith") or meta.get("totalAvailableHadith")
                if not total:
                    await interaction.followup.send("Could not determine the size of that collection. Try specifying a number.")
                    return
                number = system_random.randint(1, int(total))
            except Exception as e:
                logging.error(f"Failed to fetch collection metadata for {collection}: {e}")
                await interaction.followup.send("Failed to fetch collection info. Please try again.")
                return
            url = f"https://api.sunnah.com/v1/collections/{collection}/hadiths/{number}"
        else:
            url = f"https://api.sunnah.com/v1/collections/{collection}/hadiths/{number}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={"X-API-Key": self.config['sunnah']},
                                       timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status == 404:
                        await interaction.followup.send(f"Hadith {collection.capitalize()} {number} not found.")
                        return
                    r.raise_for_status()
                    data = await r.json()

            if 'hadith' not in data or not data['hadith']:
                await interaction.followup.send("Failed to fetch hadith. Please try again.")
                return

            final_hadith = process_hadith(data)
            final_wrapped = textwrap.wrap(final_hadith, 1024)
            final_collection = data["collection"].capitalize() if collection == "random" else collection.capitalize()
            final_number = data["hadithNumber"]
            final_grade = data['hadith'][0].get('grade') if 'hadith' in data else None

        except asyncio.TimeoutError:
            await interaction.followup.send("Request timed out. The hadith service may be slow. Please try again later.")
            return
        except aiohttp.ClientResponseError as e:
            await interaction.followup.send(f"Error accessing hadith service (HTTP {e.status}). Please try again later.")
            return
        except aiohttp.ClientError as e:
            logging.error(f"Network error fetching hadith: {e}")
            await interaction.followup.send("Network error occurred. Please try again.")
            return
        except (KeyError, IndexError, ValueError) as e:
            logging.error(f"Invalid hadith response format: {e}")
            await interaction.followup.send("Invalid response from hadith service. Please try again.")
            return

        start = time.time()
        page_list = []
        for page, text in enumerate(final_wrapped):
            page_list.append(create_hadith_embed(final_number, final_collection, text, page + 1, final_grade))

        paginator = EmbedPaginator(pages=page_list, user_id=interaction.user.id, timeout=3600)
        await paginator.send(interaction, deferred=True)

        logger.info(time.time() - start)

    @app_commands.command(name='basmalah', description="Sends a besmele.")
    async def basmalah(self, interaction: discord.Interaction):
        await interaction.response.send_message('Bismillahirrahmanirrahim')

    @app_commands.command(name='pray', description="[@mention] pray for a user or a group of users.")
    async def dua(self, interaction: discord.Interaction, user: discord.Member):
        duas = [f'O Allah, Have mercy on {user.mention} ',
                f'O Allah, Bless {user.mention} and his family ',
                f'O Allah, Grant {user.mention} passage into Paradise ',
                f'O Allah, Protect {user.mention} from Your Wrath ',
                f'O Allah, Forgive {user.mention} of his sins ',
                f'O Allah, Ease {user.mention}\'s mind '
                ]
        await interaction.response.send_message(system_random.choice(duas))

    @app_commands.command(name='salawat', description="Salawat upon the Prophet")
    async def salawat(self, interaction: discord.Interaction):
        await interaction.response.send_message('O Allah! send Your blessing upon Muhammad and the progeny of Muhammad')

    @app_commands.command(name='esma', description="Sends one of the 99 names. Chooses randomly if no number is specified.")
    @app_commands.describe(number="Pick a number between 1-99 or leave empty for a random one.")
    async def esma(self, interaction: discord.Interaction, number: int = None):
        with open(os.getcwd() + '/cogs/data/esma.json', 'r') as f:
            names = json.load(f)

        if number is None:
            response = system_random.choice(names)
        else:
            response = names[number - 1]

        await interaction.response.send_message(f'One of His Names is {response}')

    @app_commands.command(name='takbeer', description="Takbeer!")
    async def takbeer(self, interaction: discord.Interaction):
        await interaction.response.send_message("Allahuakbar")

    @app_commands.command(name='dhikr', description="Sends a reminder")
    async def dhikr(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Indeed, it is We (Allah) who created humankind and fully know what their souls whisper to them, and We are closer to "
            "them than their jugular vein (By His knowledge). (Qaf , ayah 16)")

    @app_commands.command(name='salaam', description="Send a greeting message.")
    async def salaam(self, interaction: discord.Interaction):
        await interaction.response.send_message(' wa ʿalaykumu s-salām')
