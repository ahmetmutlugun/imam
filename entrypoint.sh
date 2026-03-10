#!/bin/sh
set -e

DATA_DIR="/app/cogs/data"

# Sync small static files from image into volume on every boot.
# This ensures redeployments propagate updated data files.
cp /app/cogs/data_baked/*.json "$DATA_DIR/" 2>/dev/null || true
cp /app/cogs/data_baked/*.txt  "$DATA_DIR/" 2>/dev/null || true

# Download en_hilali.json if missing (~7MB, Quran translation)
if [ ! -f "$DATA_DIR/en_hilali.json" ]; then
    echo "Downloading en_hilali.json..."
    wget -q -O "$DATA_DIR/en_hilali.json" \
        "https://api.alquran.cloud/v1/quran/en.hilali"
    echo "en_hilali.json ready."
fi

# Generate quran_audio.txt if missing
if [ ! -f "$DATA_DIR/quran_audio.txt" ]; then
    echo "Generating quran_audio.txt (fetches ~114 API pages, takes ~30s)..."
    python3 /app/generate_audio_index.py
    echo "quran_audio.txt ready."
fi

exec python3 bot.py
