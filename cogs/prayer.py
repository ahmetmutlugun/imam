import datetime
import http.client
import json
import logging
import os
import urllib.parse

import discord
import requests
from discord.commands import slash_command, Option
from discord.ext import commands

errorText = "No prayer time found for your location. Please set a new location using imam location <city>"


def load_countries() -> "dict[str][str]":
    with open(os.getcwd() + '/cogs/data/countryCodes.json') as f:
        data = json.load(f)

    # Reverse order of countries and country codes
    country_data = {v: k for k, v in data.items()}

    return country_data


# Create a countries cache
countries = load_countries()


def set_user_data(user_id, data_name, data_value):
    try:
        f = open(os.getcwd() + '/cogs/data/data.json', 'r+')
        data = json.load(f)
        f.close()
        if user_id in data:
            data[str(user_id)][data_name] = data_value
        with open(os.getcwd() + '/cogs/data/data.json', 'w') as json_file:
            json.dump(data, json_file, indent=4)
            json_file.truncate()
    except Exception as e:
        logging.warning(e)


def get_location(author_id):
    """
    Get location
    Returns location of a user
    :param author_id: user id
    :return: city - user's city as string
    """
    with open(os.getcwd() + '/cogs/data/data.json', 'r+') as f:
        data = json.load(f)
    try:
        if str(author_id) in data:
            city = data[str(author_id)]['city']
            country = data[str(author_id)]['country']
            return [city, country]
        else:
            return ['Cupertino', 'United States of America']

    except KeyError:
        return ['Cupertino', 'United States of America']


def get_countries(ctx: discord.AutocompleteContext) -> list:
    matching_items = []
    # Iterate over the keys of the countries cache
    for item in countries:
        item_list = ctx.value.lower().split(" ")
        failed = False
        for _ in item_list:
            if _ not in item.lower():
                failed = True
        if not failed:
            matching_items.append(item)
    return matching_items


def format_city(city: str | Option) -> str:
    """ Takes a string of form 'foo bar func' and outputs a string of
    form 'FooBarFunc'

    Parameter
    ---------
    city : str
        Unformatted city name
    
    Returns
    -------
    str :
        Formatted city name
    """
    new_city = city.lower().split()
    return ''.join([c.capitalize() for c in new_city])


def get_prayer_times(city: str, country: str):
    """Returns all prayer times for a specific location

    Parameters
    ----------
    city : str
        A user's city's name
    country : str
            A user's country

    Returns
    -------
    pt : dict[str, str]
        dictionary of all prayer times
    """

    url = f'https://api.aladhan.com/v1/timingsByCity?city={city}&country={country}&method=2'
    r = requests.get(url)
    data = r.json()
    prayertimes = ['Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha', 'Midnight']
    if r.status_code != 200:
        return None
    ptl = {}
    for p in prayertimes:
        ptl.update({p: data['data']['timings'][p]})
    return ptl


def calc_local_time_offset(city: str, country: str | Option, config: dict):
    """
    Gets the local utc offset from positionstack's API
    Parameters
    ----------
    city : str
        A city name
    country : str
        A country name
    config : dict
        config.json

    Returns
    -------
    offset : str
        String representation of utc offset in seconds
    """
    # Connect to the position stack API
    conn = http.client.HTTPConnection('api.positionstack.com')

    params = urllib.parse.urlencode({
        'access_key': config['positionstack'],
        'query': city,
        'country': country,
        "output": 'json',
        'limit': 1,
        'timezone_module': 1,
    })
    try:
        conn.request('GET', '/v1/forward?{}'.format(params))
        res = conn.getresponse()
        # Obtain the utc offset from the json response
        data = res.read()
        return json.loads(data.decode('utf-8'))['data'][0]['timezone_module']['offset_sec']
    except Exception as e:
        logging.error(e)
        return None


def get_local_time_offset(author_id) -> int:
    """
    Returns local time offset of a user from data.json
    Parameters
    ---------
    author_id :
        user id
    
    Returns
    -------
    utc_offset : int
        UTC offset for the user
    """
    with open(os.getcwd() + '/cogs/data/data.json', 'r+') as f:
        data = json.load(f)
    try:
        if str(author_id) in data:
            offset = data[str(author_id)]['utc_offset']
            return offset

    except Exception:
        # Return the utc offset of Cupertino by default
        return -25200


def create_user(userid: str, iman: int, tovbe: int, city: str | Option, elham: int, utc_offset: int,
                country: str | Option):
    """
    Creates a user in the data.json
    Parameters
    ---------- 
        userid : str
           A user's discord id
        iman : int
            A user's iman as determined by the bot
        tovbe : int
            A user's tovbe count
        city : str
            A user's configured city
        elham : int
            A user's elhamdulillah count
        utc_offset : int
            A user's utc offset
        country : str
            A user's country
    """
    with open(os.getcwd() + '/cogs/data/data.json', 'r+') as f:
        data = json.load(f)

    if userid not in data:  # see if user doesn't have a saved location
        # Save user location, utc_offset, and defaults
        new_user = {"imam": iman, "tovbe": tovbe, "city": city, "elham": elham, "utc_offset": utc_offset,
                    "country": country}
        data[userid] = new_user
        with open(os.getcwd() + '/cogs/data/data.json', 'w') as json_file:  # write to data.json
            json.dump(data, json_file, indent=4)


class PrayerTimes(commands.Cog):

    def __init__(self, bot, config):
        """
        Create a PrayerTimes cog

        :param bot client
        """
        self.client = bot
        self.config = config

    @slash_command(name='location', description="Set your location for prayer commands.")
    async def location(self, ctx, city: discord.Option(str, "Pick a city"),
                       country: discord.Option(str, "Pick a country", autocomplete=get_countries)):
        """
        Changes user's location to their parameter specified location

        Parameters
        ----------
            ctx :
                Context from which location was invoked
            city : discord.Option
                 A discord option to specify a city str
            country : discord.Option
                A discord option to specify a country str
        """
        # open data.json file to read later
        with open(os.getcwd() + '/cogs/data/data.json', 'r+') as f:
            data = json.load(f)

        # Format the city properly for the API
        formatted_city = format_city(city)

        # Get the local time offset for the specified city
        print(load_countries()[country])
        utc_offset = calc_local_time_offset(formatted_city, load_countries()[country], self.config)
        if utc_offset is None:
            await ctx.respond("Your location is invalid. Please use \"\\location <City Name> <Country Name>\"")
            return

        try:
            if str(ctx.author.id) not in data:  # see if user doesn't have a saved location
                create_user(str(ctx.author.id), 1, 0, city, 0, int(utc_offset), country)
            else:
                data[str(ctx.author.id)]['city'] = city
                data[str(ctx.author.id)]['utc_offset'] = utc_offset
                data[str(ctx.author.id)]['country'] = countries[country]

                with open(os.getcwd() + '/cogs/data/data.json', 'w') as json_file:
                    json.dump(data, json_file, indent=4)
        except Exception as e:
            logging.error("Error in /location" + str(e))
        await ctx.respond(
            "User location changed to: \nCity: " + city + "\nCountry: " + country)

    @slash_command(name="prayer", description="Display a user-specified prayer time", )
    async def prayer(self, ctx, sub_command: Option(str, "Enter a Prayer option",
                                                    choices=["fajr", "dhuhr", "asr", "maghrib", "isha", "all"])):
        """
        Returns user-specified prayer time from a list of prayer times (fajr, dhuhr, etc..) using
        get_prayer_times()
        Parameters
        ----------
            ctx :
                Context from which the command was invoked
            sub_command : str
                Sub_command specifying which prayer time to return
        """
        # Get location of the user and prayer times for that location
        location = get_location(ctx.author.id)  # get user location
        city = location[0].replace("_", " ")
        country = location[1].replace("_", " ")
        time = get_prayer_times(city, country)
        # Return error message if time couldn't be found
        if time is None:
            await ctx.respond(errorText)
        if sub_command == "fajr":
            await ctx.respond("Fajr/Sahur is at " + str(time['Fajr']) + " for " + city)
        elif sub_command == "dhuhr":
            await ctx.respond("Dhuhr is at " + str(time['Dhuhr']) + " for " + city)
        elif sub_command == "asr":
            await ctx.respond("Asr is at " + str(time['Asr']) + " for " + city)
        elif sub_command == "maghrib":
            await ctx.respond("Maghrib is at " + str(time['Maghrib']) + " for " + city)
        elif sub_command == "isha":
            await ctx.respond("Isha is at " + str(time['Isha']) + " for " + city)
        elif sub_command == "all":
            string = "Prayer times for " + city + ", " + country + ":\n"

            embed = discord.Embed(title="Prayer times for " + city + ", " + country, type='rich', color=0x048c28)
            embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                                      "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")
            # Add all prayer times as embeds to the main embed
            for key in time:
                string += str(key) + ": " + str(time[key]) + "\n"
                embed.add_field(name=str(key) + ":", value=str(time[key]))
            # Respond with the embed to ctx
            await ctx.respond(embed=embed)

    @slash_command(name='prayer_now', description="Displays the current prayer time.")
    async def prayer_now(self, ctx):
        """
        Returns the current and next prayer times, and the time left until the next prayer time
        Parameters
        ----------
        ctx :
            Context from which prayer_now was invoked
        """
        # Set up lists and dictionaries
        location = get_location(ctx.author.id)  # get user location
        city = location[0].replace("_", " ")
        country = location[1].replace("_", " ")
        # Obtains dictionary from get_prayer_times() and reformats it
        prayer_times = get_prayer_times(city, country)

        # Get the local time in seconds
        local_time = datetime.timedelta(seconds=get_local_time_offset(ctx.author.id)) + datetime.datetime.utcnow()

        # Get rid of the date variables because it is messing with the comparison operation in the forloop
        formatted_time = datetime.datetime.strptime(local_time.strftime('%H:%M'), "%H:%M")

        pnow = ""
        pnext = "N/A"
        # Iterate over all prayer times and find prayertime now
        for prayer in prayer_times:
            p_time = datetime.datetime.strptime(prayer_times[prayer], "%H:%M")
            # If local time precedes p_time then 'prayer' is the next prayer
            if formatted_time < p_time:
                pnext = prayer
                break

        # If the local time is greater than Isha time and isn't midnight yet
        # TODO: refactor with match statements (if we upgrade to py 3.10)
        if pnext == "Midnight":
            pnow = "Isha"
        elif pnext == "N/A" or pnext == 'Fajr':
            pnext = "Fajr"
            pnow = "Midnight"
        # Otherwise using pnext determine pnow
        elif pnext == "Sunrise":
            pnow = "Fajr"
        elif pnext == "Dhuhr":
            pnow = "Sunrise"
        elif pnext == "Asr":
            pnow = "Dhuhr"
        elif pnext == "Maghrib":
            pnow = "Asr"
        elif pnext == "Isha":
            pnow = "Maghrib"

        # Get the prayer time for the next prayer
        p_next_time = datetime.datetime.strptime(prayer_times[pnext], "%H:%M")
        diff = abs(p_next_time - formatted_time)
        hours = diff.seconds // 3600
        mins = (diff.seconds // 60) % 60

        # Because the time loops after 23:59, this needs to be done
        if pnow == "Isha":
            hours = 23 - hours
            mins = 59 - mins

        # Return everything
        await ctx.respond("Warning: This command is under development. Please double check prayer times.")
        await ctx.respond(
            f"The current prayer for {city} is {pnow}. There are {hours} hours and {mins} minutes until {pnext}.")
