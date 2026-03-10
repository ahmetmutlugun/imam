FROM python:3.12-slim

WORKDIR /app

# ffmpeg for Quran audio, wget for entrypoint data download
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg wget \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Backup the small committed data files so entrypoint can sync them
# into the named volume on every boot (keeps them updated on redeploy)
RUN cp -r /app/cogs/data /app/cogs/data_baked

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
