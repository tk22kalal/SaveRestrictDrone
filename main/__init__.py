#Github.com/Vasusen-code

import os
import logging
import sys

from pyrogram import Client
from telethon.sync import TelegramClient

logging.basicConfig(
    format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
    level=logging.WARNING
)

# Read all config from environment variables (works on Heroku, VPS, Replit, etc.)
API_ID   = os.environ.get('API_ID', '')
API_HASH = os.environ.get('API_HASH', '')
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
SESSION  = os.environ.get('SESSION', '')   # optional - not required to start
AUTH     = int(os.environ.get('AUTH', '0'))

if not all([API_ID, API_HASH, BOT_TOKEN]):
    print("ERROR: Missing required environment variables: API_ID, API_HASH, BOT_TOKEN")
    sys.exit(1)

# Telethon bot client (always required)
bot = TelegramClient('bot', int(API_ID), API_HASH).start(bot_token=BOT_TOKEN)

# Pyrogram userbot (optional - only created when SESSION is provided)
userbot = None
if SESSION:
    userbot = Client(
        "saverestricted",
        session_string=SESSION,
        api_hash=API_HASH,
        api_id=int(API_ID)
    )
    try:
        userbot.start()
    except Exception as e:
        print(f"Userbot warning: could not start with SESSION ({e}). "
              "Users can still log in with /login.")
        userbot = None
else:
    print("No SESSION set. Userbot disabled — users must /login with their phone number.")

# Pyrogram bot client (always required)
Bot = Client(
    "SaveRestricted",
    bot_token=BOT_TOKEN,
    api_id=int(API_ID),
    api_hash=API_HASH
)
try:
    Bot.start()
except Exception as e:
    print(f"ERROR: Could not start Pyrogram bot client: {e}")
    sys.exit(1)
