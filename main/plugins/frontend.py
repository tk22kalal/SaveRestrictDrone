#Github.com/Vasusen-code

import time, os

from .. import bot as Drone
from .. import userbot, Bot, API_ID, API_HASH
from main.plugins.pyroplug import get_msg
from main.plugins.helpers import get_link, join
from main.plugins.login import get_user_session

from telethon import events
from pyrogram import Client
from pyrogram.errors import FloodWait

message = "Send me the message link you want to start saving from, as a reply to this message."


async def _get_acc(user_id: int):
    """
    Return the best available Pyrogram user client for fetching restricted content.
    Priority: 1) per-user logged-in session  2) global shared userbot
    Returns None if neither is available.
    """
    session_str = get_user_session(user_id)
    if session_str:
        try:
            acc = Client(
                f"user_{user_id}",
                session_string=session_str,
                api_id=int(API_ID),
                api_hash=API_HASH,
            )
            await acc.start()
            return acc
        except Exception as e:
            print(f"Could not start personal session for {user_id}: {e}")

    if userbot:
        return userbot

    return None


@Drone.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def clone(event):
    if event.is_reply:
        reply = await event.get_reply_message()
        if reply and reply.text == message:
            return
    try:
        link = get_link(event.text)
        if not link:
            return
    except TypeError:
        return

    edit = await event.reply("Processing!")

    # Handle invite links (join private chat)
    if 't.me/+' in link or 't.me/joinchat/' in link:
        acc = await _get_acc(event.sender_id)
        if acc is None:
            await edit.edit(
                "No user session available.\n"
                "Please use /login to log in with your phone number first."
            )
            return
        q = await join(acc, link)
        await edit.edit(q)
        personal = get_user_session(event.sender_id)
        if personal and acc is not userbot:
            try:
                await acc.stop()
            except Exception:
                pass
        return

    if 't.me/' not in link:
        return

    acc = await _get_acc(event.sender_id)
    if acc is None:
        await edit.edit(
            "No user session available.\n"
            "Please use /login to log in with your phone number first."
        )
        return

    personal = get_user_session(event.sender_id)
    try:
        try:
            await get_msg(acc, Bot, Drone, event.sender_id, edit.id, link, 0)
        except FloodWait as fw:
            x = fw.value if hasattr(fw, 'value') else fw.x
            await Drone.send_message(
                event.sender_id,
                f'Try again after {x} seconds due to floodwait from Telegram.'
            )
        except Exception as e:
            print(e)
            await Drone.send_message(
                event.sender_id,
                f"An error occurred while cloning `{link}`\n\n**Error:** {str(e)}"
            )
    finally:
        if personal and acc is not userbot:
            try:
                await acc.stop()
            except Exception:
                pass
