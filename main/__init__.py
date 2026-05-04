#Github.com/Vasusen-code

from pyrogram import Client

from telethon.sessions import StringSession
from telethon.sync import TelegramClient

from decouple import config
import logging, time, sys

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

# variables - read from environment variables
API_ID = config('API_ID', default='')
API_HASH = config('API_HASH', default='')
BOT_TOKEN = config('BOT_TOKEN', default='')
SESSION = config('SESSION', default='')
AUTH = config('AUTH', default=0, cast=int)

if not all([API_ID, API_HASH, BOT_TOKEN, SESSION]):
    print("ERROR: Missing required environment variables: API_ID, API_HASH, BOT_TOKEN, SESSION")
    sys.exit(1)

bot = TelegramClient('bot', int(API_ID), API_HASH).start(bot_token=BOT_TOKEN) 

userbot = Client("saverestricted", session_string=SESSION, api_hash=API_HASH, api_id=int(API_ID)) 

try:
    userbot.start()
except BaseException:
    print("Userbot Error ! Have you added SESSION while deploying??")
    sys.exit(1)

Bot = Client(
    "SaveRestricted",
    bot_token=BOT_TOKEN,
    api_id=int(API_ID),
    api_hash=API_HASH
)    

try:
    Bot.start()
except Exception as e:
    print(e)
    sys.exit(1)
