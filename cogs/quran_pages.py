import logging
import os
import json
import redis

import discord
from discord import app_commands, Embed
from discord.ext import commands

from cogs.paginator import EmbedPaginator

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

redis_client = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=6379)

# Cache surahs at startup — used by autocomplete on every keystroke
with open(os.getcwd() + '/cogs/data/surahs.json', 'r') as _f:
    _surahs: dict = json.load(_f)


def set_quran_redis():
    """Load Quran JSON into Redis if not already present."""
    if redis_client.exists("en_hilali"):
        return
    try:
        with open(os.getcwd() + '/cogs/data/en_hilali.json', 'r') as f:
            redis_client.json().set("en_hilali", "$", json.load(f))
    except Exception as e:
        logging.error(f"Failed to load Quran data into Redis: {e}")


def create_quran_embed(surah: int, ayah: int):
    try:
        surah_name = redis_client.json().get("en_hilali", f"$.data.surahs[{surah - 1}].englishName")
        text = redis_client.json().get("en_hilali", f"$.data.surahs[{surah - 1}].ayahs[{ayah - 1}].text")
    except AttributeError:
        return None

    if not surah_name or not text:
        return None

    embed = Embed(title=f"Surah {surah_name[0]}", type='rich', color=0x048c28)
    embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                              "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")
    embed.add_field(name="Ayah " + str(ayah), value=str(text[0]))

    return embed


async def get_surahs(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    matching_items = []
    for item in list(_surahs.values()):
        item_list = current.lower().split(" ")
        failed = False
        for _ in item_list:
            if _ not in item.lower():
                failed = True
        if not failed:
            matching_items.append(app_commands.Choice(name=item, value=item))
    return matching_items[:25]


def find_surah_id(surah: str) -> int:
    return int(list(_surahs.keys())[list(_surahs.values()).index(surah)])


class Quran_Pages(commands.Cog):
    def __init__(self, client):
        self.client = client
        set_quran_redis()

    @app_commands.command(name="quran")
    @app_commands.describe(
        surah="Select a surah",
        start_ayah="Start ayah",
        end_ayah="End ayah",
    )
    @app_commands.autocomplete(surah=get_surahs)
    async def quran(self, interaction: discord.Interaction, surah: str, start_ayah: int, end_ayah: int = -1):
        logger.info("Handling /quran")

        if start_ayah == -1:
            start_ayah = 1
            end_ayah = 286
        if end_ayah == -1:
            end_ayah = start_ayah + 1

        if end_ayah < start_ayah:
            await interaction.response.send_message(
                "Please pick an end ayah that is greater than the start ayah.")
            return

        try:
            surah_id = find_surah_id(surah)
        except ValueError:
            await interaction.response.send_message("Please pick a valid surah from the autocomplete list.")
            return

        if surah_id == -1:
            await interaction.response.send_message(
                "Could not find that surah/ayah combination. Please let us know if this is an error.")
            return

        if create_quran_embed(surah_id, start_ayah) is None:
            await interaction.response.send_message(
                "Could not find that surah/ayah combination. Please let us know if this is an error.")
            return

        page_list = []
        for i in range(start_ayah, end_ayah + 1):
            embed = create_quran_embed(surah_id, i)
            if embed is not None:
                page_list.append(embed)
            else:
                break

        paginator = EmbedPaginator(pages=page_list, user_id=interaction.user.id, timeout=3600)
        await paginator.send(interaction)
