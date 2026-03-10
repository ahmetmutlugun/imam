"""
One-time script to generate cogs/data/quran_audio.txt.

Uses the Quran.com v4 API to fetch audio file URLs for every verse.
Default reciter: Mishari Rashid al-Afasy (recitation_id=7).
Find other recitation IDs at: https://api.quran.com/api/v4/resources/recitations

Run with:
    pip install requests
    python generate_audio_index.py
"""

import json
import time
import urllib.request
import urllib.parse

RECITATION_ID = 7   # Mishari Rashid al-Afasy
OUTPUT_PATH = "cogs/data/quran_audio.txt"
TOTAL_SURAHS = 114


def fetch_surah(recitation_id: int, surah: int) -> list:
    params = urllib.parse.urlencode({"per_page": 300})
    url = f"https://api.quran.com/api/v4/recitations/{recitation_id}/by_chapter/{surah}?{params}"
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read())["audio_files"]


def main():
    all_verses = []
    for surah in range(1, TOTAL_SURAHS + 1):
        print(f"Fetching surah {surah}/{TOTAL_SURAHS}...", end="\r")
        verses = fetch_surah(RECITATION_ID, surah)
        for v in verses:
            all_verses.append({
                "verse_key": v["verse_key"],
                "url": v["url"],
            })
        time.sleep(0.1)  # be polite to the API

    with open(OUTPUT_PATH, "w") as f:
        json.dump(all_verses, f)

    print(f"\nDone. {len(all_verses)} verses written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
