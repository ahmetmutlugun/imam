import json
import random
import discord
import asyncio
import requests
import textwrap
import logging

from discord.commands import \
    slash_command, Option

from discord.ext import commands
import discord
import requests
from discord.ext import commands

f = open('data/config.json', 'r+')
config = json.load(f)
f.close()

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
    final_hadith = final_hadith.replace("<br/>", "").replace("<b>", "").replace("</b>", "").replace(
        "</p>", "").replace("<p>", " ")
    return final_hadith


def create_hadith_embed(number, collection, hadith, page):
    embed = discord.Embed(title=f"Hadith {number} from {collection} collection.", type='rich',
                          color=0x048c28)
    embed.add_field(name=f"{collection} {number}  Page {page}", value=hadith)
    embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                              "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")
    return embed


class Prayer(commands.Cog):
    def __init__(self, client):
        self.client = client
        self._last_member = None

    # TODO:
    #  - Add fasting days count
    #  - Add alhamduallah, subhanallah, allahu akbar, and shahada count
    #  - Add tahajjud count
    #  - Add quran page count

    @slash_command(name='hadith', description="Sends a hadith")
    async def hadith(self, ctx, collection: str = "random", number: int = None):
        await ctx.send("This command is under construction!")
        # if collection == "random":
        #     # Send request to sunnah.com api
        #     r = requests.get(url="https://api.sunnah.com/v1/hadiths/random",
        #                      headers={"X-API-Key": config['sunnah']})
        #     data = r.json()
        #     final_hadith = process_hadith(data)
        #     final_wrapped = textwrap.wrap(final_hadith, 1024)
        #     final_collection = data["collection"].capitalize()
        #     final_number = data["hadithNumber"]
        #
        # elif collection.lower() not in collection_names:
        #     await ctx.send(
        #         f"Your collection is not supported. Please choose from the following collections: \n {collections_str}")
        #     return
        #
        # elif number is None:
        #     await ctx.send(
        #         f"Please provide a collection name and number from the following "
        #         f"collections: \n {collections_str}\n ")
        #     return
        #
        # else:
        #     try:
        #         r = requests.get(url=f"https://api.sunnah.com/v1/collections/{collection}/hadiths/{number}",
        #                          headers={"X-API-Key": config['sunnah']})
        #         data = r.json()
        #         final_hadith = process_hadith(data)
        #         final_wrapped = textwrap.wrap(final_hadith, 1024)
        #         final_collection = collection.capitalize()
        #         final_number = number
        #     except Exception as e:
        #         await ctx.send(
        #             f"Hadith not found. If you are sure {collection.capitalize()} {number} "
        #             f"exists, contact sharpie#0317")
        #         return
        # if len(final_wrapped) >= 2:
        #     buttons = [
        #         manage_components.create_button(style=ButtonStyle.grey, label="Previous Page",
        #                                         custom_id="hadith_previous_page"),
        #         manage_components.create_button(style=ButtonStyle.green, label="Next Page",
        #                                         custom_id="hadith_next_page")
        #     ]
        #     action_row = manage_components.create_actionrow(*buttons)
        #
        #     await ctx.send(embed=create_hadith_embed(final_number, final_collection, final_wrapped[0], 1),
        #                    components=[action_row])
        #
        #     page = 0
        #     max_pages = len(final_wrapped) - 1
        #
        #     while True:
        #         try:
        #             button_ctx = await manage_components.wait_for_component(self.bot, components=action_row,
        #                                                                     timeout=600)
        #             if button_ctx.custom_id == 'hadith_previous_page':
        #                 if page > 0:
        #                     page -= 1
        #                 else:
        #                     page = max_pages
        #                 await button_ctx.edit_origin(
        #                     embed=create_hadith_embed(final_number, final_collection, final_wrapped[page], page + 1))
        #             elif button_ctx.custom_id == 'hadith_next_page':
        #                 if page < max_pages:
        #                     page += 1
        #                 else:
        #                     page = 0
        #                 await button_ctx.edit_origin(
        #                     embed=create_hadith_embed(final_number, final_collection, final_wrapped[page], page + 1))
        #
        #         except asyncio.TimeoutError:
        #             break
        #
        # else:
        #     await ctx.send(embed=create_hadith_embed(final_number, final_collection, final_hadith, 1))

    @slash_command(name='besmele', description="Sends a besmele.")
    async def besmele(self, ctx):
        await ctx.send(f'Bismillâhirrahmânirrahîm')

    @slash_command(name='pray', description="[@mention] pray for a user or a group of users.")
    async def dua(self, ctx, user_: discord.Role or discord.Member):
        duas = [f'O Allah, Have mercy on {user_.mention} ',
                f'O Allah, Bless {user_.mention} and his family ',
                f'O Allah, Grant {user_.mention} passage into Paradise ',
                f'O Allah, Protect {user_.mention} from Your Wrath ',
                f'O Allah, Forgive {user_.mention} of his sins '
                f'O Allah, Ease {user_.mention} \'s mind '
                ]
        await ctx.send(f'{random.choice(duas)}')

    @slash_command(name='salawat', description="Salawat upon the Prophet")
    async def salawat(self, ctx):
        await ctx.send(f'O Allah! send Your blessing upon Muhammad and the progeny of Muhammad')

    @slash_command(name='esma', description="Sends one of Allah\'s names. Chooses randomly if no number is specified.")
    async def esma(self, ctx, number: int = None):
        names = [f'ar-Rahman (The Most Gracious)', f'ar-Rahim (The Most Merciful)',
                 f'al-Malik (The Sovereign)', f'al-Quddus (The Holy)', f'as-Salam (The Giver of Peace)',
                 f'al-Mu\'min (The Granter of Security)', f'al-Muhaymin (The Controller)', f'al-Aziz(The Almighty)',
                 f'al-Jabbar (The Omnipotent)', f'al-Mutakabbir (The Possessor of Greatness)',
                 f'al-Khaliq (The Creator)',
                 f'al-Bari (The Initiator)', f'al-Musawwir (The Fashioner)', f'al-Ghaffar (The Absolute Forgiver)',
                 f'al-Qahhar (The Subduer)', f'al-Wahhab (The Absolute Bestower)', f'ar-Razzaq (The Provider)',
                 f'al-Fattah (The Victory Giver)',
                 f'al-Aliym (The Omniscient)', f'al-Qabid (The Restrainer)', f'al-Basit (The Extender)',
                 f'al-Khafid (The Humiliator)', f'ar-Rafi (The Exalter)', f'al-Mu\'izz (The Giver of Honor)',
                 f'al-Mudill (The Giver of Dishonor)',
                 f'as-Samiy (The Hearing)', f'al-Basir (The All-Seeing)', f'al-Hakam (The Judge)', f'al-Adl (The Just)',
                 f'al-Latiyf (The Gentle)',
                 f'al-Khabiyr (The All-Aware)', f'al-Haliym (The Forbearing)', f'al-Aziym (The Most Great)',
                 f'al-Ghafur (The Ever-Forgiving)', f'ash-Shakur (The Grateful)',
                 f'al-Aliyy (The Sublime)', f'al-Kabir (The Great)', f'al-Hafiyz (The Preserver)',
                 f'al-Muqiyt (The Nourisher)',
                 f'al-Hasiyb (The Bringer of Judgement)', f'al-Jaliyl (The Majestic)', f'al-Kariym (The Noble)',
                 f'ar-Raqiyb (The Watchful)', f'al-Mujiyb (The Responsive)',
                 f'al-Wasi (The Vast)', f'al-Hakiym (The Wise)', f'al-Wadood (The Affectionate)',
                 f'al-Majiyd (The All-Glorious)',
                 f'al-Baa\'ith (The Resurrector)', f'ash-Shahiyd (The Witness)', f'al-Haqq (The Truth)',
                 f'al-Wakiyl (The Trustee)',
                 f'al-Qawiyy (The Strong)', f'al-Matiyn (The Firm)', f'al-Waliyy (The Friend)',
                 f'al-Hamiyd (The All Praiseworthy)',
                 f'al-Muhsiy (The Accounter)', f'al-Mubdi\' (The Originator)', f'al-Mu\'iyd (The Restorer)',
                 f'al-Muhyee (The Giver of Life',
                 f'al-Mumiyt (The Bringer of Death)', f'al-Hayy (The Living)', f'al-Qayyum (The Subsisting)',
                 f'al-Wajid (The Perceiver)',
                 f'al-Majid (The Illustrious)', f'al-Wahid (The Unique)', f'al-Ahad (The One)',
                 f'as-Samad (The Eternal)',
                 f'al-Qadir (The All-Powerful)', f'al-Muqtadir (The Determiner)', f'al-Mugaddim (The Expediter)',
                 f'al-Mu\'akhhir (The Delayer)', f'al-Awwal (The First)', f'al-Akhir (The Last)',
                 f'az-Zahir (The Manifest)',
                 f'al-Batin (The Hidden)', f'al-Waali (The Patron)', f'al-Muta\'aali (The Supremely Exalted)',
                 f'al-Barr (The Good)', f'at-Tawwaab (The Ever-Returning)', f'al-Muntaqim (The Avenger)',
                 f'al-\'Afuww (The Pardoner)', f'ar-Ra\'ouf (The Kind)',
                 f'al-Maalik ul-Mulk (The Owner of all Sovereignty)',
                 f'al-Ḏuʼl-Jalāli waʼl-ʼIkrām, Dhuʼl-Jalāli waʼl-ʼIkrām (The Owner, Lord of Majesty and Honor)',
                 f'al-Muqsit (The Equitable)', f'al-Jaami\' (The Unifier)', f'al-Ghaniyy (The Rich)',
                 f'al-Mughniyy (The Enricher)',
                 f'al-Maani\' (The Defender)', f'adh-Dhaarr (The Distressor)', f'an-Naafi\' (The Benefactor)',
                 f'an-Nour (The Light)',
                 f'al-Haadi (The Guide)', f'al-Badiy (The Originator)', f'al-Baaqi (The Immutable)',
                 f'al-Waarith (The Heir)', f'ar-Rashiyd (The Guide to the Right Path)', f'as-Sabour (The Timeless)'
                 ]

        if number is None or number < 1 or number > 99:
            response = random.choice(names)
        else:
            response = names[number - 1]

        await ctx.send(f'One of His Names is {response}')
