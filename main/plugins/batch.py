#Tg:MaheshChauhan/DroneBots
#Github.com/Vasusen-code

"""
Plugin for both public & private channels!
Supports:
- Standard private channel links: t.me/c/CHATID/MSGID
- Supergroup topic links:          t.me/c/CHATID/TOPICID/MSGID
- Bot links:                        t.me/b/USERNAME/MSGID
- Public channel links:             t.me/USERNAME/MSGID
"""

import time, os, asyncio

from .. import bot as Drone
from .. import userbot, Bot, AUTH
from main.plugins.pyroplug import get_bulk_msg, get_msg
from main.plugins.helpers import get_link, screenshot
from main.plugins.login import get_user_session

from telethon import events, Button, errors
from telethon.tl.types import DocumentAttributeVideo

from pyrogram import Client
from pyrogram.errors import FloodWait

from ethon.pyfunc import video_metadata

# active_batches maps user_id -> True when cancelled / False when running
active_batches = {}


def _parse_supergroup_link(link: str):
    """
    Parse a supergroup topic link of the form:
        https://t.me/c/CHATID/TOPICID/MSGID
    Returns (chat_id, topic_id, msg_id) as ints, or None if not that format.
    """
    parts = link.rstrip("/").split("/")
    # parts: ['https:', '', 't.me', 'c', 'CHATID', 'TOPICID', 'MSGID']
    if "t.me/c/" in link and len(parts) >= 7:
        try:
            chat_id = int("-100" + parts[4])
            topic_id = int(parts[5])
            msg_id = int(parts[6].replace("?single", "").split("-")[0])
            return chat_id, topic_id, msg_id
        except (ValueError, IndexError):
            return None
    return None


def _is_in_topic(msg, topic_id: int) -> bool:
    """
    Check whether a Pyrogram message belongs to a specific supergroup topic.
    - The first message of the topic has msg.id == topic_id.
    - Subsequent messages have msg.reply_to_top_message_id == topic_id
      OR msg.reply_to_message_id == topic_id (direct reply to topic head).
    """
    if msg is None or getattr(msg, "empty", False):
        return False
    if msg.id == topic_id:
        return True
    top = getattr(msg, "reply_to_top_message_id", None)
    if top == topic_id:
        return True
    # Direct reply to topic head (no further nesting)
    rep = getattr(msg, "reply_to_message_id", None)
    if rep == topic_id and top is None:
        return True
    return False


@Drone.on(events.NewMessage(incoming=True, from_users=AUTH, pattern="/cancel"))
async def cancel(event):
    user_id = event.sender_id
    if not active_batches.get(user_id) is False:
        return await event.reply("No batch is currently running.")
    active_batches[user_id] = True
    await event.reply("Batch cancelled.")


@Drone.on(events.NewMessage(incoming=True, from_users=AUTH, pattern="/batch"))
async def _batch(event):
    if not event.is_private:
        return

    user_id = event.sender_id
    if active_batches.get(user_id) is False:
        return await event.reply(
            "A batch is already running. Use /cancel to stop it first."
        )

    async with Drone.conversation(event.chat_id, timeout=120) as conv:
        await conv.send_message(
            "Send me the message link to start from.\n\n"
            "Supports:\n"
            "• `t.me/c/CHATID/MSGID` — private channel\n"
            "• `t.me/c/CHATID/TOPICID/MSGID` — supergroup topic (will skip other topics)\n"
            "• `t.me/b/BOT/MSGID` — bot messages\n"
            "• `t.me/USERNAME/MSGID` — public channel",
            buttons=Button.force_reply(),
        )
        try:
            link_msg = await conv.get_reply()
        except Exception as e:
            await conv.send_message("Timed out or error. Please try again.")
            return

        raw_link = link_msg.text.strip() if link_msg.text else ""
        _link = get_link(raw_link) or raw_link
        if not _link:
            await conv.send_message("No valid link found.")
            return

        await conv.send_message(
            "How many files do you want to save? (max 500)",
            buttons=Button.force_reply(),
        )
        try:
            range_msg = await conv.get_reply()
        except Exception:
            await conv.send_message("Timed out. Please try again.")
            return

        try:
            value = int(range_msg.text.strip())
            if value > 500:
                await conv.send_message("Max is 500 per batch.")
                return
            if value < 1:
                await conv.send_message("Value must be at least 1.")
                return
        except ValueError:
            await conv.send_message("Range must be a number.")
            return

        active_batches[user_id] = False
        await conv.send_message(
            f"Starting batch of {value} files...\nUse /cancel to stop."
        )

    # Determine if this is a supergroup topic link
    supergroup_parsed = _parse_supergroup_link(_link)

    # Get per-user session if available, else fall back to global userbot
    user_session_str = get_user_session(user_id)
    personal_acc = None
    if user_session_str:
        from .. import API_ID, API_HASH
        try:
            personal_acc = Client(
                f"batch_user_{user_id}",
                session_string=user_session_str,
                api_id=int(API_ID),
                api_hash=API_HASH,
            )
            await personal_acc.start()
        except Exception as e:
            await Drone.send_message(user_id, f"Could not start your session: `{e}`\nFalling back to global userbot.")
            personal_acc = None

    acc = personal_acc if personal_acc else userbot

    try:
        if supergroup_parsed:
            chat_id, topic_id, start_msg_id = supergroup_parsed
            await run_supergroup_topic_batch(acc, Bot, user_id, chat_id, topic_id, start_msg_id, value)
        else:
            await run_batch(acc, Bot, user_id, _link, value)
    finally:
        if personal_acc:
            try:
                await personal_acc.stop()
            except Exception:
                pass
        active_batches.pop(user_id, None)


async def run_batch(acc, client, sender, link, _range):
    """Standard batch for non-supergroup-topic links."""
    for i in range(_range):
        if active_batches.get(sender):
            await client.send_message(sender, "Batch cancelled.")
            return

        timer = _get_timer(i, link)

        try:
            await get_bulk_msg(acc, client, sender, link, i)
        except FloodWait as fw:
            wait = int(fw.value) if hasattr(fw, 'value') else int(fw.x)
            if wait > 299:
                await client.send_message(
                    sender, "Floodwait > 5 minutes. Cancelling batch."
                )
                return
            await asyncio.sleep(wait + 5)
            try:
                await get_bulk_msg(acc, client, sender, link, i)
            except Exception:
                pass
        except Exception as e:
            print(f"Batch error at offset {i}: {e}")

        prot = await client.send_message(
            sender, f"Sleeping `{timer}s` to avoid flood..."
        )
        await asyncio.sleep(timer)
        try:
            await prot.delete()
        except Exception:
            pass

    if not active_batches.get(sender):
        await client.send_message(sender, "✅ Batch completed.")


async def run_supergroup_topic_batch(
    acc, client, sender, chat_id: int, topic_id: int, start_msg_id: int, _range: int
):
    """
    Batch for supergroup topic links.
    Iterates message IDs starting at start_msg_id and going UP.
    Skips any message that does not belong to topic_id.
    Continues until _range messages have been *successfully processed*
    or 3× _range IDs have been scanned (to avoid infinite loops).
    """
    processed = 0
    scanned = 0
    max_scan = _range * 3 + 50
    current_id = start_msg_id

    await client.send_message(
        sender,
        f"🔍 Supergroup topic batch started.\n"
        f"Chat: `{chat_id}` | Topic: `{topic_id}` | From msg: `{start_msg_id}`\n"
        f"Will collect up to **{_range}** files (skipping other topics).",
    )

    while processed < _range and scanned < max_scan:
        if active_batches.get(sender):
            await client.send_message(sender, "Batch cancelled.")
            return

        scanned += 1
        msg_id = start_msg_id + scanned - 1

        try:
            msg = await acc.get_messages(chat_id, msg_id)
        except FloodWait as fw:
            wait = int(fw.value) if hasattr(fw, 'value') else int(fw.x)
            await asyncio.sleep(wait + 3)
            try:
                msg = await acc.get_messages(chat_id, msg_id)
            except Exception:
                current_id += 1
                continue
        except Exception as e:
            print(f"Supergroup batch: error fetching {msg_id}: {e}")
            continue

        if msg is None or getattr(msg, "empty", False):
            continue

        # Skip messages not belonging to our topic
        if not _is_in_topic(msg, topic_id):
            continue

        processed += 1
        timer = _get_timer(processed, "t.me/c/")

        try:
            # get_msg requires a valid edit_id (message to update with progress)
            link_str = f"https://t.me/c/{str(chat_id).replace('-100', '')}/{msg_id}"
            status_msg = await client.send_message(sender, "Processing...")
            await get_msg(acc, client, Drone, sender, status_msg.id, link_str, 0)
        except FloodWait as fw:
            wait = int(fw.value) if hasattr(fw, 'value') else int(fw.x)
            if wait > 299:
                await client.send_message(
                    sender, "Floodwait > 5 minutes. Cancelling batch."
                )
                return
            await asyncio.sleep(wait + 5)
            try:
                status_msg2 = await client.send_message(sender, "Processing (retry)...")
                await get_msg(acc, client, Drone, sender, status_msg2.id, link_str, 0)
            except Exception:
                pass
        except Exception as e:
            print(f"Supergroup batch: error processing {msg_id}: {e}")

        if processed < _range:
            prot = await client.send_message(
                sender, f"Sleeping `{timer}s`... ({processed}/{_range} done)"
            )
            await asyncio.sleep(timer)
            try:
                await prot.delete()
            except Exception:
                pass

    if not active_batches.get(sender):
        skipped = scanned - processed
        await client.send_message(
            sender,
            f"✅ Supergroup topic batch completed!\n"
            f"**Saved:** {processed} files\n"
            f"**Skipped** (different topic or empty): {skipped}",
        )


def _get_timer(index: int, link: str) -> int:
    """Return a flood-protection sleep time based on progress and link type."""
    if "t.me/c/" not in link:
        return 2 if index < 25 else 3
    if index < 25:
        return 5
    if index < 50:
        return 10
    return 15
