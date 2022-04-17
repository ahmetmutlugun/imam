# """
# Based on music.py by EvieePy.
# https://gist.github.com/EvieePy/ab667b74e9758433b3eb806c53a19f34
# """
# import json
# import discord
# from discord.ext import commands
# import itertools
# import traceback
# from async_timeout import *
# from discord_slash.utils.manage_components import create_button, create_actionrow, wait_for_component
# from discord_slash.model import ButtonStyle
#
# FFMPEG_OPTIONS = {
#     'before_options': '-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
#     'options': '-vn -loglevel panic'
# }
#
#
# class VoiceConnectionError(commands.CommandError):
#     """Custom Exception class for connection errors."""
#
#
# class InvalidVoiceChannel(VoiceConnectionError):
#     """Exception for cases of invalid Voice Channels."""
#
#
# class AudiusSource(discord.PCMVolumeTransformer):
#
#     def __init__(self, source, *, data, requester):
#         super().__init__(source)
#         self.requester = requester
#
#         self.title = data.get('title')
#         self.web_url = data.get('webpage_url')
#
#     def __getitem__(self, item: str):
#         return self.__getattribute__(item)
#
#     @classmethod
#     async def create_source(cls, ctx, search: str, *, loop, data_input=None):
#         # loop = loop or asyncio.get_event_loop()
#         #
#         # to_run = partial(ytdl.extract_info, url=search, download=False)
#         # #data = await loop.run_in_executor(None, to_run)
#         data = {
#             "title": data_input,
#             "requester": ctx.author
#         }
#         return cls(discord.FFmpegPCMAudio(search, **FFMPEG_OPTIONS), data=data, requester=ctx.author)
#
#
# class MusicPlayer:
#     __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 'volume')
#
#     def __init__(self, ctx):
#         self.bot = ctx.bot
#         self._guild = ctx.guild
#         self._channel = ctx.channel
#         self._cog = ctx.cog
#
#         self.queue = asyncio.Queue()
#         self.next = asyncio.Event()
#
#         self.np = None  # Now playing message
#         self.volume = .5
#         self.current = None
#
#         ctx.bot.loop.create_task(self.player_loop())
#
#     async def player_loop(self):
#         await self.bot.wait_until_ready()
#
#         while not self.bot.is_closed():
#             self.next.clear()
#
#             try:
#                 # Wait for the next song. If we timeout cancel the player and disconnect...
#                 async with timeout(600):  # 10 minutes...
#                     source = await self.queue.get()
#             except asyncio.TimeoutError:
#                 return self.destroy(self._guild)
#
#             source.volume = self.volume
#             self.current = source
#
#             self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
#             self.np = await self._channel.respond(f'**Now Reciting:** {source.title} requested by '
#                                                f'{source.requester}')
#             await self.next.wait()
#
#             # Make sure the FFmpeg process is cleaned up.
#             source.cleanup()
#             self.current = None
#
#             try:
#                 # We are no longer playing this song...
#                 await self.np.delete()
#             except discord.HTTPException:
#                 pass
#
#     def destroy(self, guild):
#         return self.bot.loop.create_task(self._cog.cleanup(guild))
#
#
# def quran_audio_api(sure, ayet):
#     f = open("data/quran_audio.txt", "r+")
#     data = json.load(f)
#     f.close()
#
#     for key in data:
#         if key['verse_key'] == f"{sure}:{ayet}":
#             return f"https://download.quranicaudio.com/verses/{key['url']}"
#     return
#
#
# def create_quran_buttons(surah_and_ayah):
#     buttons = [
#
#         create_button(style=ButtonStyle.grey, label="Previous Ayah",
#                       custom_id="previous" + surah_and_ayah),
#         create_button(style=ButtonStyle.green, label="Next Ayah",
#                       custom_id="next" + surah_and_ayah),
#         create_button(style=ButtonStyle.blurple, label="Recite",
#                       custom_id="recite" + surah_and_ayah),
#         create_button(style=ButtonStyle.red, label="Close",
#                       custom_id="close" + surah_and_ayah)
#     ]
#     return buttons
#
#
# def create_quran_embed(surah, ayah):
#     f = open('data/en_hilali.json', 'r+')
#     data = json.load(f)
#     f.close()
#
#     surah_name = data["data"]["surahs"][surah - 1]["englishName"]
#     text = data["data"]["surahs"][surah - 1]["ayahs"][ayah - 1]["text"]
#
#     embed = discord.Embed(title=f"Surah {surah_name}", type='rich', color=0x048c28)
#     embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
#                                               "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")
#     embed.add_field(name="Ayah " + str(ayah), value=text)
#
#     return embed
#
#
# class Recite(commands.Cog):
#     __slots__ = ('bot', 'players')
#
#     def __init__(self, bot):
#         self.bot = bot
#         self.players = {}
#
#     async def cleanup(self, guild):
#         try:
#             await guild.voice_client.disconnect()
#         except AttributeError:
#             pass
#
#         try:
#             del self.players[guild.id]
#         except KeyError:
#             pass
#
#     async def __local_check(self, ctx):
#         if not ctx.guild:
#             raise commands.NoPrivateMessage
#         return True
#
#     async def __error(self, ctx, error):
#         if isinstance(error, commands.NoPrivateMessage):
#             try:
#                 return await ctx.respond('This command can not be used in Private Messages.')
#             except discord.HTTPException:
#                 pass
#         elif isinstance(error, InvalidVoiceChannel):
#             await ctx.respond('Error connecting to Voice Channel. '
#                            'Please make sure you are in a valid channel or provide me with one')
#
#         print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
#         traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
#
#     def get_player(self, ctx):
#         try:
#             player = self.players[ctx.guild.id]
#         except KeyError:
#             player = MusicPlayer(ctx)
#             self.players[ctx.guild.id] = player
#
#         return player
#
#     @commands.command(name='connect', aliases=['join'])
#     async def connect_(self, ctx, *, channel: discord.VoiceChannel = None):
#         if not channel:
#             try:
#                 channel = ctx.author.voice.channel
#             except AttributeError:
#                 raise InvalidVoiceChannel('No channel to join. Please either specify a valid channel or join one.')
#
#         vc = ctx.voice_client
#
#         if vc:
#             if vc.channel.id == channel.id:
#                 return
#             try:
#                 await vc.move_to(channel)
#             except asyncio.TimeoutError:
#                 raise VoiceConnectionError(f'Moving to channel: <{channel}> timed out.')
#         else:
#             try:
#                 await channel.connect()
#             except asyncio.TimeoutError:
#                 raise VoiceConnectionError(f'Connecting to channel: <{channel}> timed out.')
#
#         await ctx.respond(f'Connected to: **{channel}**', delete_after=20)
#
#     @commands.command(name='play', brief='Search or use url to queue a single track.',
#                       aliases=['read', 'recite', 'recitequran', 'readquran'])
#     async def play_(self, ctx, surah_and_ayah):
#         try:
#             array = surah_and_ayah.split(":")
#             surah = int(array[0])
#             array2 = array[1].split("-")
#             first_ayah = int(array2[0])
#             last_ayah = int(array2[1])
#             if last_ayah - first_ayah > 20:
#                 await ctx.respond("You can only request up to 20 ayah.")
#                 return
#         except Exception:
#             await ctx.respond("Please enter a valid surah/ayah in this format: Surah:firstayah-lastayah")
#             return
#
#         await ctx.trigger_typing()
#         vc = ctx.voice_client
#         if not vc:
#             await ctx.invoke(self.connect_)
#         if surah_and_ayah is not None:
#             counter = 0
#             for i in range(int(first_ayah), int(last_ayah) + 1):
#                 counter += 1
#                 player = self.get_player(ctx)
#                 source = await AudiusSource.create_source(ctx, quran_audio_api(surah, i), loop=self.bot.loop,
#                                                           data_input=f"{surah}:{i}")
#                 await player.queue.put(source)
#             if counter == 0:
#                 await ctx.respond("Please enter a valid surah/ayah in this format: 1:1-7")
#                 return
#             await ctx.respond(f"Added the following to queue: Surah {surah}:{first_ayah} to {surah}:{last_ayah}.")
#         else:
#             await ctx.respond("Please enter a valid surah/ayah in this format: 1:1-7")
#
#     @commands.command(name='pause', brief='Pause the current ayah.')
#     async def pause_(self, ctx):
#         vc = ctx.voice_client
#
#         if not vc or not vc.is_playing():
#             return await ctx.respond('I am not currently reciting anything!', delete_after=20)
#         elif vc.is_paused():
#             return
#
#         vc.pause()
#         await ctx.respond(f'**`{ctx.author}`**: Paused the song!')
#
#     @commands.command(name='resume', brief='Resume the paused ayah.')
#     async def resume_(self, ctx):
#         vc = ctx.voice_client
#
#         if not vc or not vc.is_connected():
#             return await ctx.respond('I am not currently reciting anything!', delete_after=20)
#         elif not vc.is_paused():
#             return
#
#         vc.resume()
#         await ctx.respond(f'**`{ctx.author}`**: Resumed the song!')
#
#     @commands.command(name='skip', brief='Skip the current ayah.')
#     async def skip_(self, ctx):
#         vc = ctx.voice_client
#
#         if not vc or not vc.is_connected():
#             return await ctx.respond('I am not currently reciting anything!', delete_after=20)
#
#         if vc.is_paused():
#             pass
#         elif not vc.is_playing():
#             return
#
#         vc.stop()
#         await ctx.respond(f'**`{ctx.author}`**: Skipped the song!')
#
#     @commands.command(name='queue', aliases=['q'], brief='List the next 5 ayah in the queue.')
#     async def queue_info(self, ctx):
#         vc = ctx.voice_client
#
#         if not vc or not vc.is_connected():
#             return await ctx.respond('I am not currently connected to voice!', delete_after=20)
#
#         player = self.get_player(ctx)
#         if player.queue.empty():
#             return await ctx.respond('There are currently no more queued verses.')
#
#         upcoming = list(itertools.islice(player.queue._queue, 0, 5))
#
#         fmt = '\n'.join(f'**`{_["title"]}`**' for _ in upcoming)
#         embed = discord.Embed(title=f'Upcoming - Next {len(upcoming)} out of {len(player.queue._queue)} in queue.',
#                               description=fmt)
#
#         await ctx.respond(embed=embed)
#
#     @commands.command(name='now_reading', aliases=['nr', 'current', 'reciting', 'reading', 'now_reciting'],
#                       brief="Get the ayah being recited.")
#     async def now_reading_(self, ctx):
#         vc = ctx.voice_client
#
#         if not vc or not vc.is_connected():
#             return await ctx.respond('I am not currently connected to voice!', delete_after=200)
#
#         player = self.get_player(ctx)
#         if not player.current:
#             return await ctx.respond('I am not currently reciting anything!', delete_after=200)
#
#         try:
#             # Remove our previous now_playing message.
#             await player.np.delete()
#         except discord.HTTPException:
#             pass
#
#         player.np = await ctx.respond(f'**Now Reciting:** `{vc.source.title}` '
#                                    f'requested by `{vc.source.requester}`', delete_after=200)
#
#     @commands.command(name='volume', aliases=['vol'], brief='Adjust the volume.')
#     async def change_volume(self, ctx, *, vol: float = 100.0):
#         vc = ctx.voice_client
#
#         if not vc or not vc.is_connected():
#             return await ctx.respond('I am not currently connected to voice!', delete_after=20)
#
#         if not 0 < vol < 101:
#             return await ctx.respond('Please enter a value between 1 and 100.')
#
#         player = self.get_player(ctx)
#
#         if vc.source:
#             vc.source.volume = vol / 100
#
#         player.volume = vol / 100
#         await ctx.respond(f'**`{ctx.author}`**: Set the volume to **{vol}%**')
#
#     @commands.command(name='stop', brief='Stop reciting.')
#     async def stop(self, ctx):
#         vc = ctx.voice_client
#
#         if not vc or not vc.is_connected():
#             return await ctx.respond('I am not currently reciting anything!', delete_after=20)
#
#         await self.cleanup(ctx.guild)
#
#     @commands.command(name='leave', brief="Leave the voice channel")
#     async def leave(self, ctx):
#         try:
#             vc = ctx.voice_client
#             await vc.disconnect()
#             await ctx.respond("Sadaqa Allaah al-‘Azeem.", delete_after=20)
#         except Exception:
#             await ctx.respond("I am not currently connected to any channel.", delete_after=20)
#
#     @commands.command(brief='Find a specific ayah from the Quran')
#     async def quran(self, ctx, surah_and_ayah: str):
#         f = open('data/en_hilali.json', 'r+')
#         data = json.load(f)
#         array = surah_and_ayah.split(":")
#         surah = int(array[0]) - 1
#         array2 = array[1].split("-")
#         first_ayah = int(array2[0])
#         surah_name = data["data"]["surahs"][surah]["englishName"]
#
#         if len(array2) == 1:
#             text = data["data"]["surahs"][surah]["ayahs"][first_ayah - 1]["text"]
#             embed = discord.Embed(title=f"Surah {surah_name}", type='rich', color=0x048c28)
#             embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
#                                                       "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")
#
#             # If the ayah is longer than 1024 ayahs add two fields
#             if len(str(text)) > 1024:
#                 embed.add_field(name="Ayah " + str(first_ayah) + " part 1", value=text[:(len(text)) // 2])
#                 embed.add_field(name="Ayah " + str(first_ayah) + " part 2", value=text[(len(text)) // 2:-1])
#             else:
#                 embed.add_field(name="Ayah " + str(first_ayah), value=text)
#
#             buttons = [
#                 create_button(style=ButtonStyle.grey, label="Recite",
#                               custom_id="recite" + surah_and_ayah),
#             ]
#             action_row = create_actionrow(*buttons)
#
#             await ctx.respond(embed=embed, components=[action_row])
#
#             while True:
#                 try:
#                     button_ctx = await wait_for_component(self.bot, components=action_row,
#                                                           timeout=600)
#                     if button_ctx.custom_id == "recite" + surah_and_ayah:
#                         await ctx.respond("Loading audio. This may take up to 10 seconds depending on the length.",
#                                        delete_after=10)
#                         await ctx.trigger_typing()
#                         vc = ctx.voice_client
#                         if not vc:
#                             await ctx.invoke(self.connect_)
#
#                         print(quran_audio_api(surah + 1, first_ayah))
#                         player = self.get_player(ctx)
#                         source = await AudiusSource.create_source(ctx, quran_audio_api(surah + 1, first_ayah),
#                                                                   loop=self.bot.loop,
#                                                                   data_input=f"{surah + 1}:{first_ayah}")
#                         await player.queue.put(source)
#                         await ctx.respond(
#                             f"Added the following to queue: Surah {surah + 1}:{first_ayah}.", delete_after=20)
#
#                 except asyncio.TimeoutError:
#                     break
#
#             await ctx.respond(embed=embed)
#             return
#
#         last_ayah = int(array2[1])
#
#         if last_ayah - first_ayah > 6:
#             await ctx.respond("Please do not request more than 7 ayah.")
#             return
#         embed = discord.Embed(title=f"Surah {surah_name}", type='rich', color=0x048c28)
#         for x in range(first_ayah, last_ayah + 1):
#             text = data["data"]["surahs"][surah]["ayahs"][x - 1]["text"]
#
#             # If the ayah is longer than 1024 ayahs add two fields broken up into roughly equal halves
#             if len(str(text)) > 1024:
#                 embed.add_field(name="Ayah " + str(x) + " part 1", value=text[:(len(text)) // 2])
#                 embed.add_field(name="Ayah " + str(x) + " part 2", value=text[(len(text)) // 2:-1])
#             else:
#                 embed.add_field(name="Ayah " + str(x), value=text, inline=False)
#
#         await ctx.respond(embed=embed)
#
#     @commands.command(brief='Browse a surah in the quran.', aliases=['browse', 'browsequran'])
#     async def browse_quran(self, ctx, surah_and_ayah: str):
#         array = surah_and_ayah.split(":")
#         surah = int(array[0])
#         current_ayah = int(array[1])
#
#         try:
#             embed = create_quran_embed(surah, current_ayah)
#         except IndexError:
#             await ctx.respond("Could not find that surah/ayah combination. Please let us know is this is en error.")
#             return
#
#         action_row = create_actionrow(*create_quran_buttons(surah_and_ayah))
#
#         msg = await ctx.respond(embed=embed, components=[action_row])
#
#         while True:
#             try:
#                 button_ctx = await wait_for_component(self.bot, components=action_row,
#                                                       timeout=600)
#                 if button_ctx.custom_id == 'previous' + surah_and_ayah:
#                     if current_ayah > 1:
#                         current_ayah -= 1
#                     await button_ctx.edit_origin(embed=create_quran_embed(surah, current_ayah))
#                 elif button_ctx.custom_id == 'close' + surah_and_ayah:
#                     await msg.delete()
#                     return
#                 elif button_ctx.custom_id == 'next' + surah_and_ayah:
#                     current_ayah += 1
#                     try:
#                         await button_ctx.edit_origin(embed=create_quran_embed(surah, current_ayah))
#                     except Exception:
#                         current_ayah -= 1
#                         await button_ctx.edit_origin(embed=create_quran_embed(surah, current_ayah))
#
#                 elif button_ctx.custom_id == "recite" + surah_and_ayah:
#                     await ctx.respond("Loading audio. This may take up to 10 seconds depending on the length.",
#                                    delete_after=10)
#                     await ctx.trigger_typing()
#                     vc = ctx.voice_client
#                     if not vc:
#                         await ctx.invoke(self.connect_)
#
#                     print(quran_audio_api(surah, current_ayah))
#                     player = self.get_player(ctx)
#                     source = await AudiusSource.create_source(ctx, quran_audio_api(surah, current_ayah),
#                                                               loop=self.bot.loop,
#                                                               data_input=f"{surah}:{current_ayah}")
#                     await player.queue.put(source)
#                     await ctx.respond(
#                         f"Added the following to queue: Surah {surah}:{current_ayah}.")
#
#             except asyncio.TimeoutError:
#                 break
#
#         await ctx.respond(embed=embed)
#         return
