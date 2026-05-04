#Github.com-Vasusen-code

import asyncio, time, os

from .. import bot as Drone
from main.plugins.progress import progress_for_pyrogram
from main.plugins.helpers import screenshot

from pyrogram import Client, filters
from pyrogram.errors import (
    ChannelBanned, ChannelInvalid, ChannelPrivate,
    ChatIdInvalid, ChatInvalid, PeerIdInvalid,
    MediaEmpty,
)
from pyrogram.enums import MessageMediaType
from ethon.pyfunc import video_metadata
from ethon.telefunc import fast_upload
from telethon.tl.types import DocumentAttributeVideo
from telethon import events


def thumbnail(sender):
    if os.path.exists(f'{sender}.jpg'):
        return f'{sender}.jpg'
    return None


async def _safe_edit(client, sender, edit_id, text):
    """Edit a status message only when edit_id is valid."""
    if edit_id is None:
        return None
    try:
        return await client.edit_message_text(sender, edit_id, text)
    except Exception:
        return None


async def _resolve_peer(userbot, chat):
    """
    Force Pyrogram to resolve/cache a peer so that subsequent get_messages()
    calls work even if the session has never seen this chat before.
    """
    try:
        await userbot.get_chat(chat)
    except Exception:
        pass


async def get_msg(userbot, client, bot, sender, edit_id, msg_link, i):
    """
    userbot : Pyrogram user client (personal session)
    client  : Pyrogram bot client
    bot     : Telethon bot client
    """

    round_message = False

    if "?single" in msg_link:
        msg_link = msg_link.split("?single")[0]

    parts = msg_link.rstrip("/").split("/")

    # Strip range suffix from the last segment (e.g. "22-23" → "22")
    last_seg = parts[-1].split("-")[0]
    msg_id = int(last_seg) + int(i)

    height, width, duration, thumb_path = 90, 90, 0, None

    # ── Private / supergroup / bot links ──────────────────────────────────────
    if 't.me/c/' in msg_link or 't.me/b/' in msg_link:

        if 't.me/b/' in msg_link:
            # t.me/b/USERNAME/MSGID
            chat = str(parts[-2])
        else:
            # Standard:   t.me/c/CHATID/MSGID          → parts[-2] is CHATID
            # Supergroup: t.me/c/CHATID/TOPICID/MSGID   → parts[-3] is CHATID
            if len(parts) >= 7:
                chat = int('-100' + str(parts[-3]))
            else:
                chat = int('-100' + str(parts[-2]))

        # Resolve peer before any get_messages call
        await _resolve_peer(userbot, chat)

        file = ""
        try:
            msg = await userbot.get_messages(chat, msg_id)

            # Guard against empty/None messages
            if msg is None or getattr(msg, 'empty', False):
                await _safe_edit(client, sender, edit_id, "Message not found or was deleted.")
                return

            # Text-only or webpage message — forward as text
            if not msg.media or msg.media == MessageMediaType.WEB_PAGE:
                text = getattr(msg, 'text', None) or getattr(msg, 'caption', None) or ""
                if text:
                    edit = await _safe_edit(client, sender, edit_id, "Cloning.")
                    await client.send_message(sender, text)
                    if edit:
                        await edit.delete()
                else:
                    await _safe_edit(client, sender, edit_id, "Message has no downloadable content.")
                return

            # Media message — download then re-upload
            edit = await _safe_edit(client, sender, edit_id, "Trying to Download.")
            file = await userbot.download_media(
                msg,
                progress=progress_for_pyrogram,
                progress_args=(
                    client,
                    "**DOWNLOADING:**\n",
                    edit,
                    time.time()
                )
            )
            print(file)

            if edit:
                await edit.edit('Preparing to Upload!')

            caption = msg.caption if msg.caption is not None else None

            if msg.media == MessageMediaType.VIDEO_NOTE:
                round_message = True
                data = video_metadata(file)
                height, width, duration = data["height"], data["width"], data["duration"]
                try:
                    thumb_path = await screenshot(file, duration, sender)
                except Exception:
                    thumb_path = None
                await client.send_video_note(
                    chat_id=sender,
                    video_note=file,
                    length=height, duration=duration,
                    thumb=thumb_path,
                    progress=progress_for_pyrogram,
                    progress_args=(client, '**UPLOADING:**\n', edit, time.time())
                )

            elif msg.media == MessageMediaType.VIDEO and msg.video.mime_type in ["video/mp4", "video/x-matroska"]:
                data = video_metadata(file)
                height, width, duration = data["height"], data["width"], data["duration"]
                try:
                    thumb_path = await screenshot(file, duration, sender)
                except Exception:
                    thumb_path = None
                await client.send_video(
                    chat_id=sender,
                    video=file,
                    caption=caption,
                    supports_streaming=True,
                    height=height, width=width, duration=duration,
                    thumb=thumb_path,
                    progress=progress_for_pyrogram,
                    progress_args=(client, '**UPLOADING:**\n', edit, time.time())
                )

            elif msg.media == MessageMediaType.PHOTO:
                if edit:
                    await edit.edit("Uploading photo.")
                await bot.send_file(sender, file, caption=caption)

            else:
                thumb_path = thumbnail(sender)
                await client.send_document(
                    sender,
                    file,
                    caption=caption,
                    thumb=thumb_path,
                    progress=progress_for_pyrogram,
                    progress_args=(client, '**UPLOADING:**\n', edit, time.time())
                )

            try:
                os.remove(file)
            except Exception:
                pass
            if edit:
                try:
                    await edit.delete()
                except Exception:
                    pass

        except (ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid, PeerIdInvalid) as e:
            await _safe_edit(client, sender, edit_id,
                "Cannot access this chat.\n\n"
                "Make sure the logged-in account is a member of the channel.\n"
                f"Error: `{e}`")
            return

        except Exception as e:
            print(e)
            err = str(e)
            if any(k in err for k in ("messages.SendMedia", "SaveBigFilePartRequest",
                                       "SendMediaRequest", "File size equals to 0 B")):
                try:
                    UT = time.time()
                    uploader = await fast_upload(f'{file}', f'{file}', UT, bot, edit, '**UPLOADING:**')
                    if msg.media == MessageMediaType.VIDEO and msg.video.mime_type in ["video/mp4", "video/x-matroska"]:
                        attributes = [DocumentAttributeVideo(duration=duration, w=width, h=height,
                                                             round_message=round_message, supports_streaming=True)]
                        await bot.send_file(sender, uploader, caption=caption,
                                            thumb=thumb_path, attributes=attributes, force_document=False)
                    elif msg.media == MessageMediaType.VIDEO_NOTE:
                        attributes = [DocumentAttributeVideo(duration=duration, w=width, h=height,
                                                             round_message=True, supports_streaming=True)]
                        await bot.send_file(sender, uploader, caption=caption,
                                            thumb=thumb_path, attributes=attributes, force_document=False)
                    else:
                        await bot.send_file(sender, uploader, caption=caption,
                                            thumb=thumb_path, force_document=True)
                    try:
                        os.remove(file)
                    except Exception:
                        pass
                except Exception as e2:
                    print(e2)
                    await _safe_edit(client, sender, edit_id,
                                     f'Failed to save: `{msg_link}`\n\nError: {str(e2)}')
                    try:
                        os.remove(file)
                    except Exception:
                        pass
            else:
                await _safe_edit(client, sender, edit_id,
                                 f'Failed to save: `{msg_link}`\n\nError: {err}')
                try:
                    os.remove(file)
                except Exception:
                    pass

        # Final cleanup attempt
        try:
            if file and os.path.isfile(file):
                os.remove(file)
        except Exception:
            pass

    # ── Public channel links ───────────────────────────────────────────────────
    else:
        edit = await _safe_edit(client, sender, edit_id, "Cloning.")
        # e.g. t.me/username/123 → username
        chat = msg_link.split("t.me")[1].split("/")[1]
        try:
            msg = await client.copy_message(sender, chat, msg_id)

            # None or empty → try via userbot
            if msg is None or getattr(msg, 'empty', False):
                new_link = f't.me/b/{chat}/{msg_id}'
                return await get_msg(userbot, client, bot, sender, edit_id, new_link, i)

            if edit:
                await edit.delete()

        except Exception as e:
            err = str(e)
            # WEB_PAGE or similar copy failures — try to forward text directly
            if "WEB_PAGE" in err or "WEBPAGE" in err or "MediaEmpty" in err:
                try:
                    if userbot:
                        await _resolve_peer(userbot, chat)
                        msg = await userbot.get_messages(chat, msg_id)
                        if msg and not getattr(msg, 'empty', False):
                            text = getattr(msg, 'text', None) or getattr(msg, 'caption', None) or ""
                            if text:
                                await client.send_message(sender, text)
                                if edit:
                                    await edit.delete()
                                return
                except Exception:
                    pass
            print(e)
            await _safe_edit(client, sender, edit_id,
                             f'Failed to save: `{msg_link}`\n\nError: {err}')


async def get_bulk_msg(userbot, client, sender, msg_link, i):
    x = await client.send_message(sender, "Processing!")
    await get_msg(userbot, client, Drone, sender, x.id, msg_link, i)
