import logging
import time
import json

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
    f = open('data/en_hilali.json', 'r+')
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

def get_surahs() -> list:
    """ Retrieves a list of surahs from the surahs.json file

    Returns
    -------
    list :
        A list of surahs
    """
    with open("./data/surahs.json", "w") as f:
        data = json.load(f)

    return list(data.values())

def find_surah_id(surah : str) -> int:
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
    with open("./data/surahs.json", "w") as f:
        data = json.load(f)

    # Find the surah id 
    for k, v in data:
        if v == surah:
            return k

    # Return -1 if it couldn't be found (shouldn't happen) 
    return -1


class Quran_Pages(commands.Cog):
    def __init__(self, client):
        """Creates a quran_page cog

        Parameter
        ---------
        client : 
            bot client
        """
        self.client = client
        self._last_member = None
    
    @slash_command(name="quran")
    async def quran(self, ctx, surah: Option(str, "Select a surah", choices=get_surahs()), start_ayah: Option(int, "Start ayah", min_value=1, max_value=286, default=-1), 
    end_ayah: Option(int, "End ayah", min_value=2, max_value=286, default=-1)):
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
        # Return an error message if the end_ayah is smaller than or equal to start_ayah
        elif end_ayah < start_ayah :
            await ctx.send("end_ayah must be greater than start_ayah")
            return
        # If the end ayah isn't specified, create an embed for just the start_ayah
        elif end_ayah == -1:
            end_ayah = start_ayah+1

        # Get the ayah of the surah
        surah_id = find_surah_id(surah)
        # Check if the ayah was valid for that surah 
        try:
           create_quran_embed(surah_id, start_ayah)
        except IndexError:
            await ctx.respond("Could not find that surah/ayah combination. Please let us know is this is en error.")
            logger.error("Could not find that surah/ayah combination.")
            return

        # Start a timer and initialize a list of pages
        start = time.time()
        page_list = []
        # For each ayah create a new embed and append it to the list of pages
        for i in range(start_ayah, end_ayah):
            try:
                page_list.append(create_quran_embed(surah_id, i))
            except IndexError as e:
                logging.error("Index error in /quran %s", e)
                break
        # Create the paginator and then return it
        paginator = pages.Paginator(pages=page_list)
        await paginator.respond(ctx.interaction, ephemeral=False)

        logger.info(time.time() - start)



