import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from cogs.prayer import get_local_datetime


class Date(commands.Cog):
    def __init__(self, client, config):
        self.client = client
        self.config = config

    @app_commands.command(name='hijri',
                          description="Gives the Hijri date for the current date and any holidays that are currently taking place")
    async def hijri(self, interaction: discord.Interaction):
        local_time = get_local_datetime(interaction.user.id, self.config['encrypt_key'])
        local_date = local_time.strftime("%d-%m-%Y")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.aladhan.com/v1/gToH?date={local_date}") as r:
                    r.raise_for_status()
                    data = (await r.json())['data']['hijri']
        except Exception:
            await interaction.response.send_message("Failed to fetch Hijri date. Please try again later.")
            return

        hijri_day = data['day']
        hijri_month = data['month']['en']
        hijri_year = data['year']
        holidays = data['holidays']

        resp = f"Today is the {hijri_day}"
        if hijri_day == 1:
            resp += "st"
        elif hijri_day == 2:
            resp += "nd"
        elif hijri_day == 3:
            resp += "rd"
        else:
            resp += "th"
        resp += f" day of the month of {hijri_month}, {hijri_year} years AH. "

        if holidays:
            resp += f"It is also {holidays[0]}!"

        await interaction.response.send_message(resp)
