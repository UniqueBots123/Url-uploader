import logging
import os
import asyncio
from datetime import datetime, timedelta
from plugins.config import Config
from pyrogram import Client as Ntbots
from pyrogram import filters
logging.getLogger("pyrogram").setLevel(logging.WARNING)

# Initialize the logger
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Dictionary to track user states and cooldowns
user_states = {}

async def start_task(user_id, task_duration):
    """Function to start a task and manage cooldown."""
    # Check if user is already running a task
    if user_id in user_states:
        user_state = user_states[user_id]
        if user_state["state"] == "running":
            return "Sorry dude😎\nYou can run only one task at a time"
        elif user_state["state"] == "cooldown":
            remaining_time = user_state["cooldown_until"] - datetime.now()
            if remaining_time.total_seconds() > 0:
                return "👆 See This Message And don't disturb me again 😏"

    # Mark user as running a task
    user_states[user_id] = {"state": "running"}
    await asyncio.sleep(task_duration)  # Simulate task execution

    # Start cooldown timer
    cooldown_time = timedelta(seconds=task_duration)  # Cooldown = task duration
    cooldown_until = datetime.now() + cooldown_time
    user_states[user_id] = {"state": "cooldown", "cooldown_until": cooldown_until}

    # Notify user of task completion
    return "Task completed! Timer started."

async def check_cooldown(user_id):
    """Function to check if user can send a new task."""
    if user_id in user_states and user_states[user_id]["state"] == "cooldown":
        remaining_time = user_states[user_id]["cooldown_until"] - datetime.now()
        if remaining_time.total_seconds() > 0:
            await asyncio.sleep(remaining_time.total_seconds())  # Wait for cooldown
        # Notify user that they can send a new task
        user_states.pop(user_id)  # Remove user from state tracking
        return "You Can Send Me New Task Now"

# Create bot instance
if __name__ == "__main__" :

    if not os.path.isdir(Config.DOWNLOAD_LOCATION):
        os.makedirs(Config.DOWNLOAD_LOCATION)

    plugins = dict(root="plugins")
    Ntbots = Ntbots(
        "URL UPLOADER BOT",
        bot_token=Config.BOT_TOKEN,
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        plugins=plugins)

    print("🎊 I AM ALIVE 🎊  • Support @nothing_updates")

    # Example of handling a command to start a task
    @Ntbots.on_message(filters.command("start"))
    async def handle_start(client, message):
        user_id = message.from_user.id
        response = await start_task(user_id, 10)  # Task duration is 10 seconds
        await message.reply(response)

    # Example of handling a command to check cooldown
    @Ntbots.on_message(filters.command("status"))
    async def handle_status(client, message):
        user_id = message.from_user.id
        response = await check_cooldown(user_id)
        await message.reply(response)

    Ntbots.run()
