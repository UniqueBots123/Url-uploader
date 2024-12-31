import os
import time
import math
import logging
import asyncio
import urllib.request
from telethon import TelegramClient, events, Button
from telethon.tl.types import DocumentAttributeVideo
from plugins.config import Config
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = TelegramClient('bot', Config.API_ID, Config.API_HASH).start(bot_token=Config.BOT_TOKEN)

# Progress bar
async def progress(current, total, event, start, type_of_ps):
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        progress_str = "**Downloading**: {0}%\n".format(
            round(percentage, 2))

        tmp = progress_str + \
            "**Done**: {0} of {1}\n**Speed**: {2}/s\n**ETA**: {3}\n".format(
                humanbytes(current),
                humanbytes(total),
                humanbytes(speed),
                time_formatter(estimated_total_time)
            )
        await event.edit(text=f"`{type_of_ps}`\n\n{tmp}")

def humanbytes(size):
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def time_formatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "")
    return tmp[:-2]

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply(
        f"Hi {event.sender.first_name}, I am URL Uploader Bot.\n\nSend me any direct download link, I'll upload it to telegram as file/video.",
        buttons=[
            [Button.url("Source Code", url="https://github.com/UniqueBots123/Url-uploader")],
            [Button.url("Support Group", url="https://t.me/uniquebots")]
        ]
    )

@bot.on(events.NewMessage(pattern='http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'))
async def upload(event):
    url = event.text
    
    if "|" in url:
        url, filename = url.split("|")
        url = url.strip()
        filename = filename.strip()
    else:
        filename = os.path.basename(urlparse(url).path) or 'file'

    try:
        status = await event.reply("**Downloading...**")
        start = time.time()
        
        request = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        
        with urllib.request.urlopen(request) as response:
            total_size = int(response.headers["Content-Length"])
            block_size = 8192
            downloaded_size = 0

            with open(filename, 'wb') as f:
                while True:
                    chunk = response.read(block_size)
                    if not chunk:
                        break
                    downloaded_size += len(chunk)
                    f.write(chunk)
                    await progress(
                        downloaded_size,
                        total_size,
                        status,
                        start,
                        "Downloading..."
                    )

        await status.edit("**Uploading to Telegram...**")
        start = time.time()

        if filename.lower().endswith(('.mp4', '.mkv', '.avi')):
            metadata = DocumentAttributeVideo(
                duration=0,
                w=1280,
                h=720,
                supports_streaming=True
            )
            await bot.send_file(
                event.chat_id,
                filename,
                attributes=[metadata],
                progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                    progress(d, t, status, start, "Uploading...")
                )
            )
        else:
            await bot.send_file(
                event.chat_id,
                filename,
                progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                    progress(d, t, status, start, "Uploading...")
                )
            )

        await status.delete()
        os.remove(filename)

    except Exception as e:
        await status.edit(f"**Error:** {str(e)}")
        if os.path.exists(filename):
            os.remove(filename)

print("Bot Started...")
bot.run_until_disconnected()
