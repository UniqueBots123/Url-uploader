FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y ffmpeg aria2 git wget pv jq python3-dev mediainfo && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt telethon

RUN pip install --force-reinstall brotli

RUN pip uninstall -y yt-dlp && \
    pip install yt-dlp && \
    pip install --upgrade yt-dlp

COPY . .

RUN python3 -m pip check yt-dlp
RUN yt-dlp --version

CMD ["python3", "bot.py"]
