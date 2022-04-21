import discord
from random import SystemRandom
import random
import json
import discord
from discord.ui import View
from discord.commands import slash_command
from discord.ext import commands

srandom = SystemRandom()

class TriviaButton(discord.ui.Button):
    def __init__(self, ctx, label, is_answer):
        super().__init__(style=discord.ButtonStyle.blurple, label=label)
        self.is_answer = is_answer
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        content : str
        if self.is_answer:
            self.disabled = True
            self.style = discord.ButtonStyle.success
            content = "That was the right answer"
        else:
            self.disabled = True
            self.style = discord.ButtonStyle.danger
            content = "That was not the right answer"
        
        await interaction.response.edit_message(content=content, view=None)

class TriviaView(View):

    def __init__(self, ctx, answers: "dict[str][bool]"):
        super().__init__(timeout=30)
        self.ctx = ctx

        for k, v in answers:
            self.add_item(TriviaButton(self.ctx, label=k, is_answer=v))


    async def on_timeout(self):
        self.ctx.send("Time's up! Thank you for playing")
        self.clear_items()


class Trivia(commands.Cog):

    def __init__(self, client) -> None:
        """ Creates a Trivia cog

        Parameter
        ----------
        client :
            bot client
        """
        self.client = client
        self._last_member = None
    
    @slash_command(name='trivia', description="Asks a random islamic trivia question.")
    async def trivia(self, ctx):
        await ctx.respond("This command is in construction!")
        # await ctx.respond(embed=trivia_embed[0], components=[action_row])
        #
        # author_id = str(ctx.author)
        # trivia_embed = create_trivia_embed(author_id)
        #
        # action_row = create_actionrow(*trivia_embed[1])
        # await ctx.respond(embed=trivia_embed[0], components=[action_row])
        # while True:
        #     try:
        #         button_ctx = await wait_for_component(client, components=action_row,
        #                                               timeout=600)
        #         if button_ctx.custom_id == trivia_embed[2]:
        #             await ctx.respond("That is the correct answer!", delete_after=3)
        #
        #             for _ in range(0, 10):
        #                 trivia_embed[0].remove_field(0)
        #             trivia_embed[0].add_field(name="__Questions__", value=trivia_embed[4])
        #             trivia_embed[0].add_field(name="Correct answer:", value=trivia_embed[3])
        #             await button_ctx.edit_origin(embed=trivia_embed[0], components=None)
        #             return
        #         else:
        #             await ctx.respond("That is the wrong answer! Please try again!", delete_after=3)
        #             await button_ctx.edit_origin(embed=trivia_embed[0])
        #
        #     except asyncio.TimeoutError:
        #         break


def get_random_question():
    with open('data/questions.json', 'r+') as f:
        data = json.load(f)
    return data[str(srandom.choice(range(0, len(data))))]


def create_trivia_embed():
    """
    Creates the trivia embed of a question
    """
    data = get_random_question()
    embed = discord.Embed(title='Islamic Trivia', type='rich', color=discord.Color.blue(),
                            description="Pick the answer choice that corresponds with the best answer.", )
    embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                                "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")
    embed.set_thumbnail(
        url="https://media.discordapp.net/attachments/453076515777937428/852697275716599808/IMAM-BOT-PSD.png?width"
            "=676&height=676")

    # Add question field
    embed.add_field(name="__Question__", value=data["question"], inline=False)
    # Add order of options randomly
    aliases = ["A", "B", "C", "D"]
    options = ["a", "b", "c", "d"]
    for al in aliases:
        random.shuffle(options)
        embed.add_field(name=f"*Option {al}", value=data[options.pop()], inline=False)
    
        r = str(random.randint(1, 1000))
    #     buttons = [
    #
    #         create_button(style=ButtonStyle.blurple, label="A",
    #                       custom_id=author_id + "a" + r),
    #         create_button(style=ButtonStyle.blurple, label="B",
    #                       custom_id=author_id + "b" + r),
    #         create_button(style=ButtonStyle.blurple, label="C",
    #                       custom_id=author_id + "c" + r),
    #         create_button(style=ButtonStyle.blurple, label="D",
    #                       custom_id=author_id + "d" + r)
    #     ]
    #     print(author_id + data["correct_answer"] + r)
    #
    #     return embed, buttons, author_id + data["correct_answer"] + r, data[data["correct_answer"]], data["question"]
