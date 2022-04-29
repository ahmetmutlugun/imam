import os
from random import SystemRandom
import random
import json
import discord
from discord.ui import View
from discord.commands import slash_command
from discord.ext import commands

srandom = SystemRandom()


class TriviaButton(discord.ui.Button):
    def __init__(self, ctx, label, is_answer, embed):

        super().__init__(style=discord.ButtonStyle.blurple, label=label)
        self.is_answer = is_answer
        self.ctx = ctx
        self.embed = embed

    async def callback(self, interaction: discord.Interaction):
        # If the button is the correct answer, when clicked it should change to a success
        # style and edit the original message
        self.disabled = True
        if self.is_answer:
            self.style = discord.ButtonStyle.success
            await self.ctx.send("That is the right answer!", delete_after=10)#.edit_original_message(content="That was the right answer!")
        # Otherwise, the button should change to a danger style and send a follow up message)
        else:
            self.style = discord.ButtonStyle.danger
            #await interaction.followup.send("That was not the right answer")
            await self.ctx.send("That is the wrong answer!", delete_after=10)


class TriviaView(View):

    def __init__(self, ctx, correct_answer: str, answers: "dict[str][bool]") -> None:
        """Initializes a Trivia View object

        Parameters
        ----------
            ctx :
                Context from which view is called to be displayed
            correct_answer : str
                The correct answer to the trivia question
            answers : dict[str][bool]
                A dictionary of strings and booleans of the form:
                {'a': true, 'b': false, 'c': false, 'd': false}
        """
        super().__init__(timeout=30)
        self.ctx = ctx
        self.correct_answer = correct_answer

        # Add all child components
        for i in answers:
            self.add_item(TriviaButton(self.ctx, label=i, is_answer=answers[i], embed=create_trivia_embed()))

    async def on_timeout(self) -> None:
        """ View should clear items and send a time's up message on timeout
        """
        self.clear_items()
        await self.ctx.send(f"Time's up! The answer was: {self.correct_answer}")



class Trivia(commands.Cog):

    def __init__(self, client) -> None:
        """ Creates a Trivia cog

        Parameter
        ----------
        client :
            bot client
        """
        self.client = client

    @slash_command(name='trivia', description="Asks a random islamic trivia question.")
    async def trivia(self, ctx):
        # Create embed
        embed, buttons, correct_answer = create_trivia_embed()
        # Pass buttons to trivia view class
        view = TriviaView(ctx, correct_answer, buttons)
        # Send them both to user
        await ctx.respond(content="Starting a game of trivia... You have 30 seconds!", embed=embed, view=view)


def create_trivia_embed() -> tuple:
    """Creates a trivia embed

    Returns:
    --------
        The trivia embed, the buttons dict, and the correct answer
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
    # Get randomized options and correct answer from json file
    options = [data[let] for let in 'abcd']
    random.shuffle(options)
    correct_answer = data[data['correct_answer']]
    buttons = {}

    # Iterate over the randomized options and create a dict of letters and booleans
    # a True value corresponding to the button being the correct answer choice
    for let, text in zip('abcd', options):
        embed.add_field(name=f"*Option {let}", value=text, inline=False)
        buttons[let] = (text == correct_answer)

    return embed, buttons, data[data["correct_answer"]]


def get_random_question():
    with open(os.getcwd() + '/cogs/data/questions.json', 'r+') as f:
        data = json.load(f)
    return data[str(srandom.choice(range(0, len(data))))]
