#Github.com/Vasusen-code

from pyrogram import Client

from telethon.sessions import StringSession
from telethon.sync import TelegramClient

from decouple import config
import logging, time, sys

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

# variables
API_ID = 24058425
API_HASH = "694b063e55c24287a3d30aed90191373"
BOT_TOKEN = "7361789777:AAEq1ooR7hsC8d5oRVGclmHYylAQwH7emOM"
SESSION = "BQFvGjkAMagL7iFZ_3DtnyQFVf_Zbaps424QSgZZ3_fKjqQVSxGCbWMMdXzfdaPEnZpqp0G9ZlrehS6GWXLLHuSZzjkhCN5RuVF-d3TXUlXhk4IT2uSIo7xxb6Z-LfFFlG6TzgENHMtHFePAnalx86TnzMnd-QKAxQuzRSLh4Pf7RtohuIYriir4bv4_1Ma_YScxjsKhOyZADuIV3Uzky6KdSFFVKEt7BvJIQaT73LcTLeS34dLKLb-TtOfPVxcGaRWc4jJCq_Cf039aHWllCY6Wo6hrzpdgy_DQw-79QSUOKFQ1qPKRRedUNpsTNHsB_VakpYQBeKwMpTOq4kI6tCa56WzAnAAAAAGUl4H8AA"
FORCESUB = "forcesubpavo3"
AUTH = 6356781743
DB_CHANNEL = -1002024354927
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN) 

userbot = Client("saverestricted", session_string=SESSION, api_hash=API_HASH, api_id=API_ID) 

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
