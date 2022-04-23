# """
# Based on music.py by EvieePy.
# https://gist.github.com/EvieePy/ab667b74e9758433b3eb806c53a19f34
# """
import asyncio
import json
import sys
import logging
import time

import discord
from discord.ext import commands, pages

from discord.commands import slash_command
import itertools
import traceback
from async_timeout import *

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)


FFMPEG_OPTIONS = {
    'before_options': '-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -loglevel panic'
}


class VoiceConnectionError(commands.CommandError):
    """Custom Exception class for connection errors."""


class InvalidVoiceChannel(VoiceConnectionError):
    """Exception for cases of invalid Voice Channels."""


class AudiusSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester

        self.title = data.get('title')
        self.web_url = data.get('webpage_url')

    def __getitem__(self, item: str):
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx, search: str, *, loop, data_input=None):
        # loop = loop or asyncio.get_event_loop()
        #
        # to_run = partial(ytdl.extract_info, url=search, download=False)
        # #data = await loop.run_in_executor(None, to_run)
        data = {
            "title": data_input,
            "requester": ctx.author
        }
        return cls(discord.FFmpegPCMAudio(search, **FFMPEG_OPTIONS), data=data, requester=ctx.author)


class MusicPlayer:
    __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 'volume')

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None  # Now playing message
        self.volume = .5
        self.current = None

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Wait for the next song. If we timeout cancel the player and disconnect...
                async with timeout(600):  # 10 minutes...
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self._guild)

            source.volume = self.volume
            self.current = source

            self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
            self.np = await self._channel.respond(f'**Now Reciting:** {source.title} requested by '
                                                  f'{source.requester}')
            await self.next.wait()

            # Make sure the FFmpeg process is cleaned up.
            source.cleanup()
            self.current = None

            try:
                # We are no longer playing this song...
                await self.np.delete()
            except discord.HTTPException:
                pass

    def destroy(self, guild):
        return self.bot.loop.create_task(self._cog.cleanup(guild))


def quran_audio_api(surah, ayah):

    f = open("data/quran_audio.txt", "r+")

    data = json.load(f)
    f.close()

    for key in data:
        if key['verse_key'] == f"{surah}:{ayah}":
            return f"https://download.quranicaudio.com/verses/{key['url']}"
    return


def create_quran_embed(surah: int, ayah: int) -> discord.Embed:
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
    embed: discord.Embed
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

    embed = discord.Embed(title=f"Surah {surah_name}", type='rich', color=0x048c28)
    embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                              "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")
    embed.add_field(name="Ayah " + str(ayah), value=text)

    return embed


class Recite(commands.Cog):
    __slots__ = ('bot', 'players')

    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    async def __local_check(self, ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage
        return True

    async def __error(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.respond('This command can not be used in Private Messages.')
            except discord.HTTPException:
                pass
        elif isinstance(error, InvalidVoiceChannel):
            await ctx.respond('Error connecting to Voice Channel. '
                              'Please make sure you are in a valid channel or provide me with one')

        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    def get_player(self, ctx):
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player

        return player

    @slash_command(name='connect', description="Connect")
    async def connect(self, ctx, *, channel: discord.VoiceChannel = None):
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                raise InvalidVoiceChannel('No channel to join. Please either specify a valid channel or join one.')

        vc = ctx.voice_client

        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Moving to channel: <{channel}> timed out.')
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Connecting to channel: <{channel}> timed out.')

        await ctx.respond(f'Connected to: **{channel}**', delete_after=20)

    @slash_command(name='play', description="play")
    async def play(self, ctx, surah_and_ayah):
        try:
            array = surah_and_ayah.split(":")
            surah = int(array[0])
            array2 = array[1].split("-")
            first_ayah = int(array2[0])
            last_ayah = int(array2[1])
            if last_ayah - first_ayah > 20:
                await ctx.respond("You can only request up to 20 ayah.")
                return
        except Exception:
            await ctx.respond("Please enter a valid surah/ayah in this format: Surah:firstayah-lastayah")
            return

        await ctx.trigger_typing()
        vc = ctx.voice_client
        if not vc:
            await ctx.invoke(self.connect_)
        if surah_and_ayah is not None:
            counter = 0
            for i in range(int(first_ayah), int(last_ayah) + 1):
                counter += 1
                player = self.get_player(ctx)
                source = await AudiusSource.create_source(ctx, quran_audio_api(surah, i), loop=self.bot.loop,
                                                          data_input=f"{surah}:{i}")
                await player.queue.put(source)
            if counter == 0:
                await ctx.respond("Please enter a valid surah/ayah in this format: 1:1-7")
                return
            await ctx.respond(f"Added the following to queue: Surah {surah}:{first_ayah} to {surah}:{last_ayah}.")
        else:
            await ctx.respond("Please enter a valid surah/ayah in this format: 1:1-7")

    @slash_command(name='pause', description="pause")
    async def pause(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_playing():
            return await ctx.respond('I am not currently reciting anything!', delete_after=20)
        elif vc.is_paused():
            return

        vc.pause()
        await ctx.respond(f'**`{ctx.author}`**: Paused the song!')

    @slash_command(name='resume', description="resume")
    async def resume(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.respond('I am not currently reciting anything!', delete_after=20)
        elif not vc.is_paused():
            return

        vc.resume()
        await ctx.respond(f'**`{ctx.author}`**: Resumed the song!')

    @slash_command(name='skip', description="skip")
    async def skip(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.respond('I am not currently reciting anything!', delete_after=20)

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return

        vc.stop()
        await ctx.respond(f'**`{ctx.author}`**: Skipped the song!')

    @slash_command(name='queue', description="queue")
    async def queue_info(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.respond('I am not currently connected to voice!', delete_after=20)

        player = self.get_player(ctx)
        if player.queue.empty():
            return await ctx.respond('There are currently no more queued verses.')

        upcoming = list(itertools.islice(player.queue._queue, 0, 5))

        fmt = '\n'.join(f'**`{_["title"]}`**' for _ in upcoming)
        embed = discord.Embed(title=f'Upcoming - Next {len(upcoming)} out of {len(player.queue._queue)} in queue.',
                              description=fmt)

        await ctx.respond(embed=embed)

    @slash_command(name='now_reading', description="now_reading")
    async def now_reading(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.respond('I am not currently connected to voice!', delete_after=200)

        player = self.get_player(ctx)
        if not player.current:
            return await ctx.respond('I am not currently reciting anything!', delete_after=200)

        try:
            # Remove our previous now_playing message.
            await player.np.delete()
        except discord.HTTPException:
            pass

        player.np = await ctx.respond(f'**Now Reciting:** `{vc.source.title}` '
                                      f'requested by `{vc.source.requester}`', delete_after=200)

    @slash_command(name='volume', description="volume")
    async def change_volume(self, ctx, *, vol: float = 100.0):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.respond('I am not currently connected to voice!', delete_after=20)

        if not 0 < vol < 101:
            return await ctx.respond('Please enter a value between 1 and 100.')

        player = self.get_player(ctx)

        if vc.source:
            vc.source.volume = vol / 100

        player.volume = vol / 100
        await ctx.respond(f'**`{ctx.author}`**: Set the volume to **{vol}%**')

    @slash_command(name='stop', description="stop")
    async def stop(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.respond('I am not currently reciting anything!', delete_after=20)

        await self.cleanup(ctx.guild)

    @slash_command(name='leave', description="leave")
    async def leave(self, ctx):
        try:
            vc = ctx.voice_client
            await vc.disconnect()
            await ctx.respond("Sadaqa Allaah al-‘Azeem.", delete_after=20)
        except Exception:
            await ctx.respond("I am not currently connected to any channel.", delete_after=20)

    # @slash_command(name="quran")
    async def quran(self, ctx, surah_and_ayah: str):
        logger.info("Handling /quran")
        """ Creates a series of quran embeds for a given surah starting at ayah 1

        Parameters
        ---------
        ctx : 
            A context
        
        surah_and_ayah : str
            A string containing a surah and an ayah
        """

        # Retrieve the parameters
        array = surah_and_ayah.split(":")
        surah = int(array[0])
        current_ayah = int(array[1])

        # Try creating an embed, throw an index error if the surah was invalid
        try:
           create_quran_embed(surah, current_ayah)
        except IndexError:
            await ctx.respond("Could not find that surah/ayah combination. Please let us know is this is en error.")
            logger.error("Could not find that surah/ayah combination.")
            return

        # Start a timer and initialize a list of pages
        start = time.time()
        page_list = []
        # For each ayah create a new embed and append it to the list of pages
        for i in range(1, 286):
            try:
                page_list.append(create_quran_embed(surah, i))
            except IndexError as e:
                logging.error("Index error in /quran %s", e)
                break
        # Create the paginator and then return it
        paginator = pages.Paginator(pages=page_list, timeout=3600, author_check=True, disable_on_timeout=True)
        await paginator.respond(ctx.interaction, ephemeral=False)

        logger.info(time.time() - start)
