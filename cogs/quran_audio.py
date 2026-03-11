import asyncio
import json
import os
import logging

import discord
from discord.ext import commands
from discord import app_commands
from async_timeout import timeout

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

# Cache both data files at startup
with open(os.getcwd() + '/cogs/data/en_hilali.json', 'r') as _f:
    _quran_data: dict = json.load(_f)

with open(os.getcwd() + '/cogs/data/quran_audio.txt', 'r') as _f:
    _audio_index: dict = {item['verse_key']: item['url'] for item in json.load(_f)}

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
    async def create_source(cls, interaction: discord.Interaction, search: str, *, loop, data_input=None):
        data = {
            "title": data_input,
            "requester": interaction.user
        }
        return cls(discord.FFmpegPCMAudio(search, **FFMPEG_OPTIONS), data=data, requester=interaction.user)


class MusicPlayer:
    __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 'volume')

    def __init__(self, interaction: discord.Interaction, cog):
        self.bot = interaction.client
        self._guild = interaction.guild
        self._channel = interaction.channel
        self._cog = cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None
        self.volume = .5
        self.current = None

        self.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                async with timeout(600):
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self._guild)

            source.volume = self.volume
            self.current = source

            self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
            self.np = await self._channel.send(f'**Now Reciting:** {source.title} requested by '
                                               f'{source.requester}')
            await self.next.wait()

            source.cleanup()
            self.current = None

            try:
                await self.np.delete()
            except discord.HTTPException:
                pass

    def destroy(self, guild):
        return self.bot.loop.create_task(self._cog.cleanup(guild))


def quran_audio_api(surah, ayah):
    url = _audio_index.get(f"{surah}:{ayah}")
    return f"https://download.quranicaudio.com/verses/{url}" if url else None


def create_quran_embed(surah: int, ayah: int) -> discord.Embed:
    try:
        surah_name = _quran_data["data"]["surahs"][surah - 1]["englishName"]
        text = _quran_data["data"]["surahs"][surah - 1]["ayahs"][ayah - 1]["text"]
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

    def get_player(self, interaction: discord.Interaction):
        try:
            player = self.players[interaction.guild.id]
        except KeyError:
            player = MusicPlayer(interaction, self)
            self.players[interaction.guild.id] = player
        return player

    @app_commands.command(name='connect', description="Connect to your voice channel")
    async def connect(self, interaction: discord.Interaction, channel: discord.VoiceChannel = None):
        if not channel:
            try:
                channel = interaction.user.voice.channel
            except AttributeError:
                await interaction.response.send_message(
                    'No channel to join. Please either specify a valid channel or join one.')
                return

        vc = interaction.guild.voice_client

        if vc:
            if vc.channel.id == channel.id:
                await interaction.response.send_message('Already connected.', delete_after=5)
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                await interaction.response.send_message(f'Moving to channel: <{channel}> timed out.')
                return
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                await interaction.response.send_message(f'Connecting to channel: <{channel}> timed out.')
                return

        await interaction.response.send_message(f'Connected to: **{channel}**', delete_after=20)

    @app_commands.command(name='play', description="Play Quran audio (format: surah:firstayah-lastayah)")
    async def play(self, interaction: discord.Interaction, surah_and_ayah: str):
        try:
            array = surah_and_ayah.split(":")
            surah = int(array[0])
            array2 = array[1].split("-")
            first_ayah = int(array2[0])
            last_ayah = int(array2[1])
            if last_ayah - first_ayah > 20:
                await interaction.response.send_message("You can only request up to 20 ayah.")
                return
        except Exception:
            await interaction.response.send_message(
                "Please enter a valid surah/ayah in this format: Surah:firstayah-lastayah")
            return

        await interaction.response.defer()

        try:
            await interaction.user.voice.channel.connect()
        except (asyncio.TimeoutError, discord.ClientException):
            pass

        for i in range(int(first_ayah), int(last_ayah) + 1):
            player = self.get_player(interaction)
            source = await AudiusSource.create_source(interaction, quran_audio_api(surah, i),
                                                      loop=self.bot.loop,
                                                      data_input=f"{surah}:{i}")
            await player.queue.put(source)
        await interaction.followup.send(
            f"Added the following to queue: Surah {surah}:{first_ayah} to {surah}:{last_ayah}.")

    @app_commands.command(name='pause', description="Pause recitation")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client

        if not vc or not vc.is_playing():
            return await interaction.response.send_message('I am not currently reciting anything!', delete_after=20)
        elif vc.is_paused():
            return await interaction.response.send_message('Already paused.', delete_after=5)

        vc.pause()
        await interaction.response.send_message(f'**`{interaction.user}`**: Paused the recitation!')

    @app_commands.command(name='resume', description="Resume recitation")
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client

        if not vc or not vc.is_connected():
            return await interaction.response.send_message('I am not currently reciting anything!', delete_after=20)
        elif not vc.is_paused():
            return await interaction.response.send_message('Not paused.', delete_after=5)

        vc.resume()
        await interaction.response.send_message(f'**`{interaction.user}`**: Resumed the recitation!')

    @app_commands.command(name='skip', description="Skip the current ayah")
    async def skip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client

        if not vc or not vc.is_connected():
            return await interaction.response.send_message('I am not currently reciting anything!', delete_after=20)

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return await interaction.response.send_message('Nothing is playing.', delete_after=5)

        vc.stop()
        await interaction.response.send_message(f'**`{interaction.user}`**: Skipped!')

    @app_commands.command(name='queue', description="Show the current queue")
    async def queue_info(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client

        if not vc or not vc.is_connected():
            return await interaction.response.send_message('I am not currently connected to voice!', delete_after=20)

        player = self.get_player(interaction)
        if player.queue.empty():
            return await interaction.response.send_message('There are currently no more queued verses.')

        import itertools
        upcoming = list(itertools.islice(player.queue._queue, 0, 5))

        fmt = '\n'.join(f'**`{_["title"]}`**' for _ in upcoming)
        embed = discord.Embed(title=f'Upcoming - Next {len(upcoming)} out of {len(player.queue._queue)} in queue.',
                              description=fmt)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='now_reading', description="Show what is currently being recited")
    async def now_reading(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client

        if not vc or not vc.is_connected():
            return await interaction.response.send_message('I am not currently connected to voice!', delete_after=200)

        player = self.get_player(interaction)
        if not player.current:
            return await interaction.response.send_message('I am not currently reciting anything!', delete_after=200)

        try:
            await player.np.delete()
        except discord.HTTPException:
            pass

        await interaction.response.send_message(f'**Now Reciting:** `{vc.source.title}` '
                                                f'requested by `{vc.source.requester}`', delete_after=200)
        player.np = await interaction.original_response()

    @app_commands.command(name='volume', description="Change the volume")
    async def change_volume(self, interaction: discord.Interaction, vol: float = 100.0):
        vc = interaction.guild.voice_client

        if not vc or not vc.is_connected():
            return await interaction.response.send_message('I am not currently connected to voice!', delete_after=20)

        if not 0 < vol < 101:
            return await interaction.response.send_message('Please enter a value between 1 and 100.')

        player = self.get_player(interaction)

        if vc.source:
            vc.source.volume = vol / 100

        player.volume = vol / 100
        await interaction.response.send_message(f'**`{interaction.user}`**: Set the volume to **{vol}%**')

    @app_commands.command(name='stop', description="Stop recitation and clear the queue")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client

        if not vc or not vc.is_connected():
            return await interaction.response.send_message('I am not currently reciting anything!', delete_after=20)

        await self.cleanup(interaction.guild)
        await interaction.response.send_message('Stopped.', delete_after=10)

    @app_commands.command(name='leave', description="Disconnect from voice channel")
    async def leave(self, interaction: discord.Interaction):
        try:
            vc = interaction.guild.voice_client
            await vc.disconnect()
            await interaction.response.send_message("Sadaqa Allaah al-'Azeem.", delete_after=20)
        except Exception:
            await interaction.response.send_message("I am not currently connected to any channel.", delete_after=20)
