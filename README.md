# Imam Bot

A Discord bot for Islamic content — prayer times, Quran recitation, hadith, and more.

## Commands

### Prayer & Dhikr
| Command | Description |
|---|---|
| `/prayer` | Show all prayer times for your location |
| `/prayer_now` | Current prayer and time until next |
| `/location` | Set your location for prayer times |
| `/hadith` | Random or specific hadith by collection and number |
| `/basmalah` | Send the Basmala |
| `/salawat` | Send salawat upon the Prophet |
| `/esma` | One of Allah's 99 names (random or by number) |
| `/dua` | Pray for a user |
| `/takbeer` | Allahu Akbar |
| `/dhikr` | Send a dhikr reminder |
| `/salaam` | Send a greeting |

### Quran
| Command | Description |
|---|---|
| `/play` | Queue ayahs for recitation (e.g. `2:255`) |
| `/connect` | Join a voice channel |
| `/leave` | Leave the voice channel |
| `/pause` / `/resume` | Pause or resume recitation |
| `/skip` | Skip the current ayah |
| `/stop` | Stop recitation |
| `/queue` | Show the next 5 ayahs in queue |
| `/now_reading` | Show the ayah currently being recited |
| `/change_volume` | Adjust playback volume |

### Other
| Command | Description |
|---|---|
| `/trivia` | Random Islamic trivia question |

## Setup

1. Clone the repo and install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Set your bot token in the environment and run the bot.

## License

See [Privacy Policy](Privacy.md) and [Terms of Service](TOS.md).
