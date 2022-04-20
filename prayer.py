import datetime
import json
import logging
import http.client
import urllib.parse
import discord
import requests
from discord.ext import commands
from discord.commands import slash_command

errorText = "No prayer time found for your location. Please set a new location using imam location <city>"

f = open('data/config.json', 'r+')
config = json.load(f)
f.close()


def set_user_data(userID, dataName, dataValue):
    try:
        f = open('data/data.json', 'r+')
        data = json.load(f)
        f.close()
        if userID in data:
            data[str(userID)][dataName] = dataValue
        with open('data/data.json', 'w') as json_file:
            json.dump(data, json_file, indent=4)
            json_file.truncate()
    except Exception as e:
        # logging.error(e)
        print(e)


def get_location(author_id):
    """Get location
    Returns location of a user
    :param author_id: user id
    :return: city - user's city as string
    """
    f = open('data/data.json', 'r+')
    data = json.load(f)
    f.close()
    try:
        if str(author_id) in data:
            city = data[str(author_id)]['city']
            country = data[str(author_id)]['country']
            return [city, country]
        else:
            return ['Cupertino', 'United States of America']

    except KeyError:
        # logging.error(e)
        return ['Cupertino', 'United States of America']


def get_prayer_times(city: str, country: str) -> "dict[str, str]":
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
    pt = {}
    for p in prayertimes:
        pt[p] = data['data']['timings'][p]
    return pt


def calc_local_time_offset(city: str, country: str) -> str:
    """Gets the local utc offset from positionstack's API

    Parameters
    ----------
    city : str
        A city name 
    country : str
        A country name

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
    except Exception:
        return None


def get_local_time_offset(author_id) -> int:
    """Returns local time offset of a user from data.json
    
    Parameters
    ---------
    author_id : 
        user id
    
    Returns
    -------
    utc_offset : int
        UTC offset for the user
    """
    with open('data/data.json', 'r+') as f:
        data = json.load(f)
    try:
        if str(author_id) in data:
            offset = data[str(author_id)]['utc_offset']
            return offset

    except Exception:
        # Return the utc offset of Cupertino by default
        return -25200


def create_user(userid: str, iman: int, tovbe: int, city: str, elham: int, utc_offset: int, country: str):
    """ Creates a user in the data.json

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
    with open('data/data.json', 'r+') as f:
        data = json.load(f)

    if userid not in data:  # see if user doesn't have a saved location
        # Save user location, utc_offset, and defaults
        new_user = {"imam": iman, "tovbe": tovbe, "city": city, "elham": elham, "utc_offset": utc_offset,
                    "country": country}
        data[userid] = new_user
        with open('data/data.json', 'w') as json_file:  # write to data.json
            json.dump(data, json_file, indent=4)


class PrayerTimes(commands.Cog):

    def __init__(self, bot):
        """
        Create a PrayerTimes cog
        :param bot client
        """
        self.client = bot
        self._last_member = None

    @slash_command(name='location', description="Set your location for prayer commands. imam location <city>")
    async def location(self, ctx, city: discord.Option(str, "Pick a city"), country: discord.Option(str, "Pick a country")):
        """Changes user's location to their parameter specified location

        Parameters
        ----------
            ctx : 
                Context
            city : discord.Option
                 A discord option to specify a city str
            country : discord.Option 
                A discord option to specify a country str 
        """
        # open data.json file to read later
        with open('data/data.json', 'r+') as f:
            data = json.load(f)

        with open('data/countyCodes.json', 'r+') as cc:
            countryData = json.load(cc)
        if country not in countryData:
            await ctx.respond("Please enter a valid country code.")
            return

        # Get the local time offset for the specified city
        utc_offset = calc_local_time_offset(city, country)
        if utc_offset is None:
            await ctx.respond("Your location is invalid. Please use \"\\location <CityName> <CountryName>\"")
            return

        try:
            if str(ctx.author.id) not in data:  # see if user doesn't have a saved location
                create_user(str(ctx.author.id), 1, 0, city, 0, utc_offset, country)
            else:
                data[str(ctx.message.author.id)]['city'] = city
                data[str(ctx.message.author.id)]['utc_offset'] = utc_offset
                data[str(ctx.message.author.id)]['country'] = countryData[country]
                with open('data/data.json', 'w') as json_file:
                    json.dump(data, json_file, indent=4)
        except Exception as e:
            logging.error(e)
            print(e)
        await ctx.respond(
            "User location changed to: \nCity: " + city + "\nCountry: " + countryData[country])

    @slash_command(name='fajr', description="Displays the fajr time.")
    async def fajr(self, ctx):
        """
        Returns fajr prayer time using get_prayer_times()'s prayer_times
        :param ctx: Context
        :return: string of fajr prayer time
        """
        location = get_location(ctx.author.id)  # get user location
        city = location[0].replace("_", " ")
        country = location[1].replace("_", " ")
        time = get_prayer_times(city, country)
        if time is None:
            await ctx.respond(errorText)
        else:
            await ctx.respond("Fajr/Sahur is at " + str(time['Fajr']) + " for " + city)

    @slash_command(name='dhuhr', description="Displays the dhuhr time.")
    async def dhuhr(self, ctx):
        """
        Returns dhuhr prayer time using get_prayer_times()'s prayer_times
        :param ctx: Context
        :return: string of dhuhr prayer time
        """
        location = get_location(ctx.author.id)  # get user location
        city = location[0].replace("_", " ")
        country = location[1].replace("_", " ")
        time = get_prayer_times(city, country)
        if time is None:
            await ctx.respond(errorText)
        else:
            await ctx.respond("Dhuhr is at " + str(time['Dhuhr']) + " for " + city)

    @slash_command(name='asr', description="Displays the Asr time.")
    async def asr(self, ctx):
        """
        Returns asr prayer time using get_prayer_times()'s prayer_times
        :param ctx: Context
        :return: string of asr prayer time
        """
        location = get_location(ctx.author.id)  # get user location
        city = location[0].replace("_", " ")
        country = location[1].replace("_", " ")
        time = get_prayer_times(city, country)
        if time is None:
            await ctx.respond(errorText)
        else:
            await ctx.respond("Asr is at " + str(time['Asr']) + " for " + city)

    @slash_command(name='maghrib', description="Displays the maghrib time.")
    async def maghrib(self, ctx):
        """
        Returns maghrib prayer time using get_prayer_times()'s prayer_times
        :param ctx: Context
        :return: string of maghrib prayer time
        """
        location = get_location(ctx.author.id)  # get user location
        city = location[0].replace("_", " ")
        country = location[1].replace("_", " ")
        time = get_prayer_times(city, country)
        if time is None:
            await ctx.respond(errorText)
        else:
            await ctx.respond("Maghrib is at " + str(time['Maghrib']) + " for " + city)

    @slash_command(name='isha', description="Displays the isha time.")
    async def isha(self, ctx):
        """
        Returns isha prayer time using get_prayer_times()'s prayer_times
        :param ctx: Context
        :return: string of isha prayer time
        """
        location = get_location(ctx.author.id)  # get user location
        city = location[0].replace("_", " ")
        country = location[1].replace("_", " ")
        time = get_prayer_times(city, country)
        if time is None:
            await ctx.respond(errorText)
        else:
            await ctx.respond("Isha is at " + str(time['Isha']) + " for " + city)

    @slash_command(name='prayer_times', description="Displays all prayer times.")
    async def prayer_times(self, ctx):
        """
        Returns all prayer times as a string using get_prayer_times()
        :param ctx: Context
        :return: string of all prayer times
        """
        # Set up lists and dictionaries
        location = get_location(ctx.author.id)  # get user location
        city = location[0].replace("_", " ")
        country = location[1].replace("_", " ")

        # Obtains dictionary from get_prayer_times() and reformats it
        prayer_times = get_prayer_times(city, country)
        # Creates a returnable string of all the prayer times
        string = "Prayer times for " + city + ", " + country + ":\n"

        embed = discord.Embed(title="Prayer times for " + city + ", " + country, type='rich', color=0x048c28)
        embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                                  "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")

        for key in prayer_times:
            string += str(key) + ": " + str(prayer_times[key]) + "\n"
            embed.add_field(name=str(key) + ":", value=str(prayer_times[key]))
        await ctx.respond(embed=embed)

    @slash_command(name='prayer_now', description="Displays the current prayer time.")
    async def pnow(self, ctx):
        """
        Returns the current and next prayer times, and the time left until the next prayer time
        :param ctx: Context
        :return: String of current & next prayer time + time left
        """
        # Set up lists and dictionaries
        location = get_location(ctx.author.id)  # get user location
        city = location[0].replace("_", " ")
        country = location[1].replace("_", " ")
        # Obtains dictionary from webscrape() and reformats it
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