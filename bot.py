import os
import time
import math
import asyncio
import logging
from datetime import datetime
from config import Config
from telethon import TelegramClient, events, Button
from plugins.script import Translation
from helper_funcs.display_progress import progress_for_pyrogram, humanbytes
from helper_funcs.help_uploadbot import DownLoadFile
from database.database import Database

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self):
        self.active_tasks = {}  # {user_id: task_start_time}
        self.cooldowns = {}     # {user_id: (end_time, last_message_id)}

    async def can_start_task(self, client, user_id, chat_id):
        # Check if user has an active task
        if user_id in self.active_tasks:
            await client.send_message(
                chat_id,
                "Sorry dude😎\nYou can run only one task at a time"
            )
            return False

        # Check if user is in cooldown
        if user_id in self.cooldowns:
            cooldown_end, last_msg_id = self.cooldowns[user_id]
            if time.time() < cooldown_end:
                await client.send_message(
                    chat_id,
                    "👆 See This Message And don't disturb me again 😏",
                    reply_to=last_msg_id
                )
                return False

        return True

    def start_task(self, user_id):
        self.active_tasks[user_id] = time.time()

    def end_task(self, user_id, task_duration):
        if user_id in self.active_tasks:
            del self.active_tasks[user_id]
            # Set cooldown period equal to task duration
            cooldown_end = time.time() + task_duration
            return cooldown_end

    async def set_cooldown(self, client, user_id, chat_id, cooldown_end, message_id):
        self.cooldowns[user_id] = (cooldown_end, message_id)
        
        # Schedule message for when cooldown ends
        await asyncio.sleep(cooldown_end - time.time())
        if user_id in self.cooldowns and self.cooldowns[user_id][0] == cooldown_end:
            await client.send_message(
                chat_id,
                "You Can Send Me New Task Now"
            )
            del self.cooldowns[user_id]

class Bot(object):
    def __init__(self):
        self.client = TelegramClient('bot', Config.TG_API_ID, Config.TG_API_HASH)
        self.client.start(bot_token=Config.TG_BOT_TOKEN)
        self.db = Database(Config.DATABASE_URL)
        self.task_manager = TaskManager()

    async def send_message_handler(self):
        # ... (keep existing command handlers for /start, /help, /about)

        @self.client.on(events.NewMessage(pattern=r'https?://[^\s]+'))
        async def url_handler(event):
            user_id = event.sender_id
            chat_id = event.chat_id

            # Check if user can start a new task
            if not await self.task_manager.can_start_task(self.client, user_id, chat_id):
                return

            url = event.text.strip()
            
            # Send initial processing message
            status_message = await event.reply(
                Translation.CHECK_LINK,
                buttons=[Button.inline("⛔️ Close", data="close")]
            )
            
            try:
                # Mark task as started
                self.task_manager.start_task(user_id)
                
                download_location = Config.DOWNLOAD_LOCATION + "/"
                start_time = time.time()
                
                # Download the file
                downloaded_file = await DownLoadFile(
                    url=url,
                    file_name=download_location,
                    progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                        progress_for_pyrogram(
                            d, t,
                            status_message,
                            start_time,
                            Translation.DOWNLOAD_START
                        )
                    )
                )
                
                if downloaded_file is None:
                    await status_message.edit(text=Translation.DOWNLOAD_FAILED)
                    return
                
                # Get custom thumbnail
                thumb_image = await self.db.get_thumbnail(event.sender_id)
                
                # Upload file
                await self.client.send_file(
                    event.chat_id,
                    downloaded_file,
                    thumb=thumb_image if thumb_image else None,
                    caption=Translation.CUSTOM_CAPTION_UL_FILE,
                    progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                        progress_for_pyrogram(
                            d, t,
                            status_message,
                            start_time,
                            Translation.UPLOAD_START
                        )
                    )
                )
                
                # Cleanup
                try:
                    os.remove(downloaded_file)
                except:
                    pass
                
                end_time = time.time()
                task_duration = end_time - start_time
                
                completion_msg = await status_message.edit(
                    Translation.AFTER_SUCCESSFUL_UPLOAD_MSG_WITH_TS.format(
                        time.strftime("%H:%M:%S", time.gmtime(task_duration))
                    )
                )

                # Set cooldown based on task duration
                cooldown_end = self.task_manager.end_task(user_id, task_duration)
                
                # Schedule cooldown and notification
                asyncio.create_task(
                    self.task_manager.set_cooldown(
                        self.client,
                        user_id,
                        chat_id,
                        cooldown_end,
                        completion_msg.id
                    )
                )
                
            except Exception as e:
                logger.error(str(e))
                await status_message.edit(text=Translation.DOWNLOAD_FAILED)
                self.task_manager.end_task(user_id, 0)  # Clear task on failure

        # ... (keep existing handlers for /showthumb, /delthumb, etc.)

    def run(self):
        """Run the bot."""
        logger.info("Bot Started!")
        
        if not os.path.isdir(Config.DOWNLOAD_LOCATION):
            os.makedirs(Config.DOWNLOAD_LOCATION)
        
        self.client.loop.run_until_complete(self.send_message_handler())
        self.client.run_until_disconnected()

if __name__ == "__main__":
    uploader_bot = Bot()
    uploader_bot.run()
