import os
from random import SystemRandom
import random
import json
import discord
from discord.ui import View
from discord import app_commands
from discord.ext import commands

srandom = SystemRandom()


class TriviaButton(discord.ui.Button):
    def __init__(self, label, is_answer):
        super().__init__(style=discord.ButtonStyle.green, label=label)
        self.is_answer = is_answer

    async def callback(self, interaction: discord.Interaction):
        if self.is_answer:
            self.style = discord.ButtonStyle.success
            self.view.stop()
            await interaction.response.edit_message(content=" ✅ That was the right answer!", embed=None, view=None)
        else:
            self.style = discord.ButtonStyle.danger
            self.disabled = True
            await interaction.response.edit_message(content="❌ That was not the right answer!", view=self.view)


class TriviaView(View):

    def __init__(self, interaction: discord.Interaction, correct_answer: str, answers: "dict[str][bool]") -> None:
        super().__init__(timeout=30)
        self.interaction = interaction
        self.correct_answer = correct_answer

        for i in answers:
            self.add_item(TriviaButton(label=i, is_answer=answers[i]))

    async def on_timeout(self) -> None:
        self.clear_items()
        self.stop()
        try:
            await self.interaction.followup.send(f"Time's up! The answer was: {self.correct_answer}")
        except discord.HTTPException:
            # The interaction webhook token may have expired (50027).
            pass


class Trivia(commands.Cog):

    def __init__(self, client) -> None:
        self.client = client

    @app_commands.command(name='trivia', description="Asks a random islamic trivia question.")
    @app_commands.guild_only()
    async def trivia(self, interaction: discord.Interaction):
        embed, buttons, correct_answer = create_trivia_embed()
        view = TriviaView(interaction, correct_answer, buttons)
        await interaction.response.send_message(content="Starting a game of trivia... You have 30 seconds!", embed=embed, view=view)


def create_trivia_embed() -> tuple:
    data = get_random_question()
    embed = discord.Embed(title='Islamic Trivia', type='rich', color=discord.Color.blue(),
                          description="Pick the answer choice that corresponds with the best answer.")
    embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                              "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")
    embed.set_thumbnail(
        url="https://media.discordapp.net/attachments/453076515777937428/852697275716599808/IMAM-BOT-PSD.png?width"
            "=676&height=676")

    embed.add_field(name="__Question__", value=data["question"], inline=False)
    options = [data[let] for let in 'abcd']
    random.shuffle(options)
    correct_answer = data[data['correct_answer']]
    buttons = {}

    for let, text in zip('abcd', options):
        embed.add_field(name=f"*Option {let}", value=text, inline=False)
        buttons[let] = (text == correct_answer)

    return embed, buttons, data[data["correct_answer"]]


def get_random_question():
    with open(os.getcwd() + '/cogs/data/questions.json', 'r+') as f:
        data = json.load(f)
    return data[str(srandom.choice(range(0, len(data))))]
