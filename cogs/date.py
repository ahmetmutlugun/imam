import discord
import requests
import datetime
from discord.commands import slash_command
from discord.ext import commands

from cogs.prayer import get_local_time_offset


class Date(commands.Cog):
    def __init__(self, client, config):
        """Prayer
        Create Prayer Cog
        param: client bot client
        """
        self.client = client
        self.config = config

    @slash_command(name='hijri',
                   description="Gives the Hijri date for the current date and any holidays that are currently taking place")
    async def hijri(self, ctx, ):
        local_time = datetime.timedelta(
            seconds=get_local_time_offset(ctx.author.id, self.config['encrypt_key'])) + datetime.datetime.utcnow()
        local_date = local_time.strftime("%d-%m-%Y")
        r = requests.get(url=f"http://api.aladhan.com/v1/gToH?date={local_date}")
        data = r.json()['data']['hijri']

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

        await ctx.respond(resp)
