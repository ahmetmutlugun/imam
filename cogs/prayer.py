import datetime
import hashlib
import json
import logging
import os
import zoneinfo

import aiohttp
import discord
import redis
from cryptography.fernet import Fernet
from discord import app_commands
from discord.ext import commands

# Redis client for user data
_redis = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=6379, decode_responses=True)
_USER_TTL = 2592000  # 30 days


def load_countries() -> "dict[str][str]":
    with open(os.getcwd() + '/cogs/data/countryCodes.json') as f:
        data = json.load(f)
    for k, v in data.items():
        data[k] = data[k] + f" ({k})"
    return {v: k for k, v in data.items()}


# Create a countries cache
countries = load_countries()


def decrypt(value, key):
    cipher = Fernet(key)
    return str(cipher.decrypt(bytes(str(value), encoding='utf8')).decode("utf-8"))


def _user_key(author_id) -> str:
    return f"imam:user:{hashlib.sha256(str(author_id).encode()).hexdigest()}"


def _save_user(key: str, userid, city: str, utc_offset: int, country: str, timezone_name: str = None):
    """Create or update user data in Redis with a 30-day TTL."""
    cipher = Fernet(bytes(key, encoding='utf8'))
    ukey = _user_key(userid)
    mapping = {
        'city': cipher.encrypt(bytes(city, encoding='utf8')).decode(),
        'country': cipher.encrypt(bytes(country, encoding='utf8')).decode(),
        'utc_offset': cipher.encrypt(bytes(str(utc_offset), encoding='utf8')).decode(),
    }
    if timezone_name:
        mapping['timezone_name'] = cipher.encrypt(bytes(timezone_name, encoding='utf8')).decode()
    _redis.hset(ukey, mapping=mapping)
    _redis.expire(ukey, _USER_TTL)


def get_location(author_id, key):
    """Returns [city, country] for a user, or Cupertino defaults."""
    data = _redis.hgetall(_user_key(author_id))
    if not data:
        return ['Cupertino', 'United States of America']
    try:
        return [decrypt(data['city'], key), decrypt(data['country'], key)]
    except KeyError:
        return ['Cupertino', 'United States of America']


def get_local_time_offset(author_id, key) -> int:
    """Returns the stored UTC offset in seconds. Use get_local_datetime for DST-aware time."""
    data = _redis.hgetall(_user_key(author_id))
    if not data:
        return -25200
    try:
        return int(decrypt(data['utc_offset'], key))
    except Exception:
        return -25200


def get_local_datetime(author_id, key) -> datetime.datetime:
    """Returns the user's current local time. DST-aware when an IANA timezone name is stored."""
    data = _redis.hgetall(_user_key(author_id))
    if data and 'timezone_name' in data:
        try:
            tz_name = decrypt(data['timezone_name'], key)
            return datetime.datetime.now(zoneinfo.ZoneInfo(tz_name)).replace(tzinfo=None)
        except Exception:
            pass
    # Fall back to stored UTC offset
    offset = -25200
    if data and 'utc_offset' in data:
        try:
            offset = int(decrypt(data['utc_offset'], key))
        except Exception:
            pass
    return (datetime.timedelta(seconds=offset) +
            datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None))


async def get_countries(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    matching_items = []
    for item in countries:
        item_list = current.lower().split(" ")
        failed = False
        for _ in item_list:
            if _ not in item.lower():
                failed = True
        if not failed:
            matching_items.append(app_commands.Choice(name=item, value=item))
    return matching_items[:25]


def format_city(city) -> str:
    new_city = city.lower().split()
    return ' '.join([c.capitalize() for c in new_city])


async def get_prayer_times(city: str, country: str):
    """Returns all prayer times for a specific location, or None on failure."""
    url = f'https://api.aladhan.com/v1/timingsByCity?city={city}&country={country}&method=2'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                if r.status != 200:
                    return None
                data = await r.json()
    except aiohttp.ClientError as e:
        logging.error(f"Failed to fetch prayer times for {city}, {country}: {e}")
        return None
    prayertimes = ['Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha', 'Midnight']
    return {p: data['data']['timings'][p] for p in prayertimes}


async def calc_local_time_offset(city: str, country, config: dict) -> "tuple[int | None, str | None]":
    """
    Returns (utc_offset_seconds, iana_timezone_name) for a city.
    Returns (None, None) if the location could not be resolved.
    """
    params = {
        'access_key': config['positionstack'],
        'query': city,
        'country': country,
        "output": 'json',
        'limit': 1,
        'timezone_module': 1,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.positionstack.com/v1/forward', params=params) as response:
                response.raise_for_status()
                data = await response.json()

        if data.get('data') and len(data['data']) > 0:
            tz_data = data['data'][0].get('timezone_module')
            if tz_data and 'offset_sec' in tz_data:
                return tz_data['offset_sec'], tz_data.get('name')

        logging.warning(f"No timezone data found for {city}, {country}")
        return None, None

    except aiohttp.ClientResponseError as e:
        # Don't log the exception itself: its message includes the full
        # request URL, which contains the API key.
        logging.error(f"API request failed for {city}, {country}: HTTP {e.status} {e.message}")
        return None, None
    except (KeyError, IndexError, ValueError) as e:
        logging.error(f"Invalid API response format for {city}, {country}: {e}")
        return None, None


class PrayerTimes(commands.Cog):

    def __init__(self, bot, config):
        self.client = bot
        self.config = config

    @app_commands.command(name='location', description="Set your location for prayer commands.")
    @app_commands.describe(city="Pick a city", country="Pick a country")
    @app_commands.autocomplete(country=get_countries)
    async def location(self, interaction: discord.Interaction, city: str, country: str):
        if country not in countries:
            await interaction.response.send_message("Please pick a country from the autocomplete list!")
            return

        formatted_city = format_city(city)
        utc_offset, timezone_name = await calc_local_time_offset(formatted_city, countries[country], self.config)
        if utc_offset is None:
            await interaction.response.send_message(
                "Your location is invalid. Please use \"\\location <City Name> <Country Name>\"")
            return

        try:
            _save_user(self.config['encrypt_key'], interaction.user.id, city, int(utc_offset), country, timezone_name)
        except Exception as e:
            logging.error(f"Error saving user location for {interaction.user.id}: {e}")
            await interaction.response.send_message("An error occurred while saving your location. Please try again later.")
            return
        await interaction.response.send_message(
            "User location changed to: \nCity: " + city + "\nCountry: " + country)

    @app_commands.command(name="prayer", description="Display a user-specified prayer time")
    @app_commands.describe(sub_command="Enter a Prayer option")
    @app_commands.choices(sub_command=[
        app_commands.Choice(name=c, value=c) for c in ["fajr", "dhuhr", "asr", "maghrib", "isha", "all"]
    ])
    async def prayer(self, interaction: discord.Interaction, sub_command: str):
        location = get_location(interaction.user.id, self.config['encrypt_key'])
        city = location[0].replace("_", " ")
        country = location[1].replace("_", " ")
        time = await get_prayer_times(city, country)
        if time is None:
            await interaction.response.send_message(
                "No prayer time found for your location. Please set a new location using imam location <city>")
            return
        if sub_command == "fajr":
            await interaction.response.send_message("Fajr/Sahur is at " + str(time['Fajr']) + " for " + city)
        elif sub_command == "dhuhr":
            await interaction.response.send_message("Dhuhr is at " + str(time['Dhuhr']) + " for " + city)
        elif sub_command == "asr":
            await interaction.response.send_message("Asr is at " + str(time['Asr']) + " for " + city)
        elif sub_command == "maghrib":
            await interaction.response.send_message("Maghrib is at " + str(time['Maghrib']) + " for " + city)
        elif sub_command == "isha":
            await interaction.response.send_message("Isha is at " + str(time['Isha']) + " for " + city)
        elif sub_command == "all":
            embed = discord.Embed(title="Prayer times for " + city + ", " + country, type='rich', color=0x048c28)
            embed.set_author(name="ImamBot", icon_url="https://ipfs.blockfrost.dev/ipfs"
                                                      "/QmbfvtCdRyKasJG9LjfTBaTXAgJv2whPg198vCFAcrgdPQ")
            for key in time:
                embed.add_field(name=str(key) + ":", value=str(time[key]))
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name='prayer_now', description="Displays the current prayer time.")
    async def prayer_now(self, interaction: discord.Interaction):
        location = get_location(interaction.user.id, self.config['encrypt_key'])
        city = location[0].replace("_", " ")
        country = location[1].replace("_", " ")
        prayer_times = await get_prayer_times(city, country)

        if prayer_times is None:
            await interaction.response.send_message(
                "Failed to get prayer times for your location. Please try setting a new location using /location or try again later.")
            return

        local_time = get_local_datetime(interaction.user.id, self.config['encrypt_key'])
        formatted_time = datetime.datetime.strptime(local_time.strftime('%H:%M'), "%H:%M")

        pnow = ""
        pnext = "N/A"
        for prayer in prayer_times:
            p_time = datetime.datetime.strptime(prayer_times[prayer], "%H:%M")
            if prayer == "Midnight" and p_time < datetime.datetime.strptime("12:00", "%H:%M"):
                p_time = p_time + datetime.timedelta(days=1)
            if formatted_time < p_time:
                pnext = prayer
                break

        match pnext:
            case "Midnight":
                pnow = "Isha"
            case "N/A":
                pnow = "Midnight"
                pnext = "Fajr"
            case "Fajr":
                pnow = "Midnight"
            case "Sunrise":
                pnow = "Fajr"
            case "Dhuhr":
                pnow = "Sunrise"
            case "Asr":
                pnow = "Dhuhr"
            case "Maghrib":
                pnow = "Asr"
            case "Isha":
                pnow = "Maghrib"

        p_next_time = datetime.datetime.strptime(prayer_times[pnext], "%H:%M")
        diff = abs(p_next_time - formatted_time)
        hours = diff.seconds // 3600
        mins = (diff.seconds // 60) % 60

        if pnext == "Fajr" and pnow == "Midnight":
            tomorrow = datetime.datetime.now().date() + datetime.timedelta(days=1)
            next_prayer_datetime = datetime.datetime.combine(tomorrow, p_next_time.time())
            current_datetime = datetime.datetime.combine(datetime.datetime.now().date(), formatted_time.time())
            diff = next_prayer_datetime - current_datetime
            hours = diff.seconds // 3600
            mins = (diff.seconds // 60) % 60
        elif pnext == "Midnight" and datetime.datetime.strptime(prayer_times["Midnight"], "%H:%M") < datetime.datetime.strptime("12:00", "%H:%M"):
            tomorrow = datetime.datetime.now().date() + datetime.timedelta(days=1)
            midnight_time = datetime.datetime.strptime(prayer_times["Midnight"], "%H:%M").time()
            next_prayer_datetime = datetime.datetime.combine(tomorrow, midnight_time)
            current_datetime = datetime.datetime.combine(datetime.datetime.now().date(), formatted_time.time())
            diff = next_prayer_datetime - current_datetime
            hours = diff.seconds // 3600
            mins = (diff.seconds // 60) % 60

        await interaction.response.send_message(
            f"The current prayer for {city} is {pnow}. There are {hours} hours and {mins} minutes until {pnext}.")
