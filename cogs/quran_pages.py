import logging
import os
import time
import json

import discord
from discord.ext import commands, pages
from discord import Option, Embed
from discord.commands import slash_command

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)


def create_quran_embed(surah: int, ayah: int) -> Embed:
    """ Creates an embed for a quran surah and ayah

    Parameters
    ----------
    surah : int
        The surah number
    ayah: int
        The ayah number of the surah
    
    Raises
    ------
    IndexError:
        Raised if the surah number is invalid or the ayah number
    
    Returns
    -------
    embed: Embed
        An embed containing the quran surah and ayah

    """
    f = open(os.getcwd() + '/cogs/data/en_hilali.json', 'r+')

    data = json.load(f)
    f.close()

    try:
        surah_name = data["data"]["surahs"][surah - 1]["englishName"]
        text = data["data"]["surahs"][surah - 1]["ayahs"][ayah - 1]["text"]
    except IndexError as e:
        raise e

    embed = Embed(title=f"Surah {surah_name}", type='rich', color=0x048c28)
    embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                              "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")
    embed.add_field(name="Ayah " + str(ayah), value=text)

    return embed


def get_surahs(ctx: discord.AutocompleteContext) -> list:
    """ Retrieves a list of surahs from the surahs.json file

    Returns
    -------
    list :
        A list of surahs
    """
    with open(os.getcwd() + '/cogs/data/surahs.json', "r") as f:
        data = json.load(f)

    matching_items = []
    for item in list(data.values()):
        item_list = ctx.value.lower().split(" ")
        failed = False
        for _ in item_list:
            if _ not in item.lower():
                failed = True
        if not failed:
            matching_items.append(item)
    return matching_items


def get_ayah(ctx: discord.AutocompleteContext) -> list:
    value = ctx.value
    try:
        if int(value) < 287:
            return list(range(1, int(ctx.value) + 1))
        else:
            return list(range(1, 287))
    except ValueError:
        return list(range(1, 287))


def find_surah_id(surah: str) -> int:
    """ Finds a given surah's id

    Parameter
    ---------
    surah : str
        A surah's name
    
    Returns
    -------
    int
        A surah's id
    """
    with open(os.getcwd() + '/cogs/data/surahs.json', "r") as f:
        data = json.load(f)

    # Find the surah id
    logging.error(list(data.keys())[list(data.values()).index(surah)])
    return int(list(data.keys())[list(data.values()).index(surah)])
    # print(data)
    # counter = 0
    # for i in data:
    #     counter += 1
    #     if i == surah:
    #         print(counter)
    #         return counter
    #
    # # Return -1 if it couldn't be found (shouldn't happen)
    # return -1


class Quran_Pages(commands.Cog):
    def __init__(self, client):
        """Creates a quran_page cog

        Parameter
        ---------
        client : 
            bot client
        """
        self.client = client

    @slash_command(name="quran")
    async def quran(self, ctx, surah: Option(str, "Select a surah", autocomplete=get_surahs),
                    start_ayah: Option(int, "Start ayah"),
                    end_ayah: Option(int, "End ayah", default=-1)):
        logger.info("Handling /quran")
        """ Creates a series of quran embeds for a given surah starting at start_ayah

        Parameters
        ---------
        ctx : 
            A context
        surah : str
            A surah of the user's choice
        start_ayah : int
            The starting ayah, set to -1 by default
        end_ayah : int
            The ending ayah, set to -1 by default
        """

        # If no ayah was specified create an embed for the entire surah
        if start_ayah == -1:
            start_ayah = 1
            end_ayah = 286
        # If the end ayah isn't specified, create an embed for just the start_ayah
        if end_ayah == -1:
            end_ayah = start_ayah + 1

        # Return an error message if the end_ayah is smaller than or equal to start_ayah
        if end_ayah < start_ayah:
            await ctx.respond("Please pick an end ayah that is greater than the start ayah.")
            return

        # Get the ayah of the surah
        try:
            surah_id = find_surah_id(surah)
        except ValueError:
            await ctx.respond("Please pick a valid surah from the autocomplete list.")
            return
        if surah_id == -1:
            await ctx.respond("Could not find that surah/ayah combination. Please let us know is this is en error.")
            return
        # Check if the ayah was valid for that surah 
        try:
            create_quran_embed(surah_id, start_ayah)
        except IndexError:
            await ctx.respond("Could not find that surah/ayah combination. Please let us know is this is en error.")
            return

        # Start a timer and initialize a list of pages
        start = time.time()
        page_list = []
        # For each ayah create a new embed and append it to the list of pages
        for i in range(start_ayah, end_ayah + 1):
            try:
                page_list.append(create_quran_embed(surah_id, i))
            except IndexError as e:
                logging.error("Index error in /quran %s %s", e, i)
                break
        # Create the paginator and then return it
        print(page_list)
        paginator = pages.Paginator(pages=page_list, timeout=3600, author_check=True, disable_on_timeout=True)
        await paginator.respond(ctx.interaction, ephemeral=False)

        logger.info(time.time() - start)
