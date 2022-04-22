import json
import os
import time
import requests
import textwrap
import logging
import re

from random import SystemRandom

import discord
from discord.commands import slash_command, Option
from discord.ext import commands, pages

srandom = SystemRandom()

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

collection_names = {
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
    'hisn'
}

collections_str = "ahmad, bukhari, muslim, tirmidhi, abudawud, nasai, ibnmajah, malik, riyadussalihin, adab, " \
                  "bulugh, shamail, mishkat, qudsi40, nawawi40, hisn "


def process_hadith(hadith_json):
    final_hadith = hadith_json['hadith'][0]['body']
    html_tags = re.compile(r'<[^>]+>')
    return html_tags.sub('', final_hadith).replace('`', '')


def create_hadith_embed(number: int, collection: str, hadith: str, page: int, grade: str) -> discord.Embed:
    """ Creates a hadith embed given the following parameters

    Parameters
    ----------
    number : int
        The hadith number in the collection
    collection : str
        The name of the hadith collection
    hadith : str
        The actual hadith text
    page : int
        The page number after the hadith has been paginated
    
    Returns
    -------
    embed : discord.Embed
        A hadith embed
    """
    embed = discord.Embed(title=f"Hadith {number} from {collection} collection.", type='rich',
                          color=0x048c28)
    embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                              "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")
    embed.add_field(name=f"{collection} {number}  Page {page}", value=hadith)
    
    embed.add_field(name="Grade", value=grade)
    return embed


class Dua(commands.Cog):
    def __init__(self, client, config):
        """Prayer
        Create Prayer Cog
        param: client bot client
        """
        self.client = client
        self._last_member = None
        self.config = config

    # TODO:
    #  - Add fasting days count
    #  - Add alhamduallah, subhanallah, allahu akbar, and shahada count
    #  - Add tahajjud count
    #  - Add quran page count

    @slash_command(name='hadith', description="Sends a hadith")
    async def hadith(self, ctx, collection: Option(str, "Enter a collection option", choices=collection_names, default="random"), number: int = None):
        """ Sends a hadith embed to the context from which it was called

        Parameters
        ---------
        self : Prayer
            Prayer object
        ctx : 
            The context from which the command was invoked
        collection : str
            Specifies what collection to request a hadith from, set to
            'random' by default 
        number: int
            Specifies the hadith number, set to None by default.
        """
        await ctx.respond("This command is under construction!")

        # If no collection was specified get a random hadith
        if collection == "random":
            # Send request to sunnah.com api
            r = requests.get(url="https://api.sunnah.com/v1/hadiths/random",
            headers={"X-API-Key": self.config['sunnah']})
            data = r.json()
            final_hadith = process_hadith(data)
            final_wrapped = textwrap.wrap(final_hadith, 1024)
            final_collection = data["collection"].capitalize()
            final_number = data["hadithNumber"]
            final_grade = None
            if "grade" in data:
                final_grade = data['hadith'][0]['grade']

        # If the collection name is not in the list of collection_names return a helpful
        # error message
        elif collection.lower() not in collection_names:
            await ctx.respond(
                f"Your collection is not supported. Please choose from the following collections: \n {collections_str}")
            return

        # If the number of the hadith is not specified, return a helpful error message
        elif number is None:
            await ctx.respond(
                f"Please provide a collection name and number from the following "
                f"collections: \n {collections_str}\n ")
            return

        # Otherwise try to reach the hadith API 
        else:
            try:
                r = requests.get(url=f"https://api.sunnah.com/v1/collections/{collection}/hadiths/{number}",

                                 headers={"X-API-Key": self.config['sunnah']})
                data = r.json()
                # Clean the JSON response
                final_hadith = process_hadith(data)
                final_wrapped = textwrap.wrap(final_hadith, 1024)
                final_collection = collection.capitalize()
                final_number = data["hadithNumber"]
                final_grade = None
                if "grade" in data:
                    final_grade = data['hadith'][0]['grade']

            except Exception:
                await ctx.respond(
                    f"Hadith not found. If you are sure {collection.capitalize()} {number} "
                    f"exists, contact sharpie#0317")
                return

        # Start a timer and initialize a list of pages
        start = time.time()
        page_list = []
        # For each ayah create a new embed and append it to the list of pages
        for page, text in enumerate(final_wrapped):
            page_list.append(create_hadith_embed(final_number, final_collection, text, page+1, final_grade))

        # Create the paginator and then return it
        paginator = pages.Paginator(pages=page_list)
        await paginator.respond(ctx.interaction, ephemeral=False)

        logger.info(time.time() - start)

    @slash_command(name='besmele', description="Sends a besmele.")
    async def besmele(self, ctx):
        await ctx.respond('Bismillâhirrahmânirrahîm')

    @slash_command(name='pray', description="[@mention] pray for a user or a group of users.")
    async def dua(self, ctx, user_: discord.Role or discord.Member):
        duas = [f'O Allah, Have mercy on {user_.mention} ',
                f'O Allah, Bless {user_.mention} and his family ',
                f'O Allah, Grant {user_.mention} passage into Paradise ',
                f'O Allah, Protect {user_.mention} from Your Wrath ',
                f'O Allah, Forgive {user_.mention} of his sins '
                f'O Allah, Ease {user_.mention} \'s mind '
                ]
        await ctx.respond(srandom.choice(duas))

    @slash_command(name='salawat', description="Salawat upon the Prophet")
    async def salawat(self, ctx):
        await ctx.respond('O Allah! send Your blessing upon Muhammad and the progeny of Muhammad')

    @slash_command(name='esma', description="Sends one of Allah\'s names. Chooses randomly if no number is specified.")
    async def esma(self, ctx, number: Option(int, min_value=1, max_value=99, default=None)):
        names = ['ar-Rahman (The Most Gracious)', 'ar-Rahim (The Most Merciful)',
                 'al-Malik (The Sovereign)', 'al-Quddus (The Holy)', 'as-Salam (The Giver of Peace)',
                 'al-Mu\'min (The Granter of Security)', 'al-Muhaymin (The Controller)', 'al-Aziz(The Almighty)',
                 'al-Jabbar (The Omnipotent)', 'al-Mutakabbir (The Possessor of Greatness)',
                 'al-Khaliq (The Creator)',
                 'al-Bari (The Initiator)', 'al-Musawwir (The Fashioner)', 'al-Ghaffar (The Absolute Forgiver)',
                 'al-Qahhar (The Subduer)', 'al-Wahhab (The Absolute Bestower)', 'ar-Razzaq (The Provider)',
                 'al-Fattah (The Victory Giver)',
                 'al-Aliym (The Omniscient)', 'al-Qabid (The Restrainer)', 'al-Basit (The Extender)',
                 'al-Khafid (The Humiliator)', 'ar-Rafi (The Exalter)', 'al-Mu\'izz (The Giver of Honor)',
                 'al-Mudill (The Giver of Dishonor)',
                 'as-Samiy (The Hearing)', 'al-Basir (The All-Seeing)', 'al-Hakam (The Judge)', 'al-Adl (The Just)',
                 'al-Latiyf (The Gentle)',
                 'al-Khabiyr (The All-Aware)', 'al-Haliym (The Forbearing)', 'al-Aziym (The Most Great)',
                 'al-Ghafur (The Ever-Forgiving)', 'ash-Shakur (The Grateful)',
                 'al-Aliyy (The Sublime)', 'al-Kabir (The Great)', 'al-Hafiyz (The Preserver)',
                 'al-Muqiyt (The Nourisher)',
                 'al-Hasiyb (The Bringer of Judgement)', 'al-Jaliyl (The Majestic)', 'al-Kariym (The Noble)',
                 'ar-Raqiyb (The Watchful)', 'al-Mujiyb (The Responsive)',
                 'al-Wasi (The Vast)', 'al-Hakiym (The Wise)', 'al-Wadood (The Affectionate)',
                 'al-Majiyd (The All-Glorious)',
                 'al-Baa\'ith (The Resurrector)', 'ash-Shahiyd (The Witness)', 'al-Haqq (The Truth)',
                 'al-Wakiyl (The Trustee)',
                 'al-Qawiyy (The Strong)', 'al-Matiyn (The Firm)', 'al-Waliyy (The Friend)',
                 'al-Hamiyd (The All Praiseworthy)',
                 'al-Muhsiy (The Accounter)', 'al-Mubdi\' (The Originator)', 'al-Mu\'iyd (The Restorer)',
                 'al-Muhyee (The Giver of Life',
                 'al-Mumiyt (The Bringer of Death)', 'al-Hayy (The Living)', 'al-Qayyum (The Subsisting)',
                 'al-Wajid (The Perceiver)',
                 'al-Majid (The Illustrious)', 'al-Wahid (The Unique)', 'al-Ahad (The One)',
                 'as-Samad (The Eternal)',
                 'al-Qadir (The All-Powerful)', 'al-Muqtadir (The Determiner)', 'al-Mugaddim (The Expediter)',
                 'al-Mu\'akhhir (The Delayer)', 'al-Awwal (The First)', 'al-Akhir (The Last)',
                 'az-Zahir (The Manifest)',
                 'al-Batin (The Hidden)', 'al-Waali (The Patron)', 'al-Muta\'aali (The Supremely Exalted)',
                 'al-Barr (The Good)', 'at-Tawwaab (The Ever-Returning)', 'al-Muntaqim (The Avenger)',
                 'al-\'Afuww (The Pardoner)', 'ar-Ra\'ouf (The Kind)',
                 'al-Maalik ul-Mulk (The Owner of all Sovereignty)',
                 'al-Ḏuʼl-Jalāli waʼl-ʼIkrām, Dhuʼl-Jalāli waʼl-ʼIkrām (The Owner, Lord of Majesty and Honor)',
                 'al-Muqsit (The Equitable)', 'al-Jaami\' (The Unifier)', 'al-Ghaniyy (The Rich)',
                 'al-Mughniyy (The Enricher)',
                 'al-Maani\' (The Defender)', 'adh-Dhaarr (The Distressor)', 'an-Naafi\' (The Benefactor)',
                 'an-Nour (The Light)',
                 'al-Haadi (The Guide)', 'al-Badiy (The Originator)', 'al-Baaqi (The Immutable)',
                 'al-Waarith (The Heir)', 'ar-Rashiyd (The Guide to the Right Path)', 'as-Sabour (The Timeless)'
                 ]

        if number is None:
            response = srandom.choice(names)
        else:
            response = names[number - 1]

        await ctx.respond(f'One of His Names is {response}')

    @slash_command(name='takbeer', description="Takbeer!")
    async def takbeer(self, ctx):
        await ctx.respond("Allahuakbar")
    
    @slash_command(name='dhikr', description="Sends a reminder")
    async def dhikr(ctx):
        await ctx.respond(
            "Indeed, it is We (Allah) who created humankind and fully know what their souls whisper to them, and We are closer to "
            "them than their jugular vein (By His knowledge). (Qaf , ayah 16)")

    @slash_command(name='salaam', description="Send a greeting message.")
    async def salaam(ctx):
        await ctx.respond(' wa ʿalaykumu s-salām')
