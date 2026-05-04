#Github.com/Vasusen-code
# Feature: Login with phone number (per-user session management)

import json
import os
import asyncio

from .. import bot as Drone, API_ID, API_HASH
from telethon import events

from pyrogram import Client
from pyrogram.errors import (
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    FloodWait,
)

SESSIONS_FILE = "user_sessions.json"


def _load_sessions():
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_sessions(sessions: dict):
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f, indent=2)


def get_user_session(user_id: int):
    """Return stored session string for user, or None."""
    sessions = _load_sessions()
    return sessions.get(str(user_id))


def set_user_session(user_id: int, session_string: str):
    sessions = _load_sessions()
    sessions[str(user_id)] = session_string
    _save_sessions(sessions)


def clear_user_session(user_id: int):
    sessions = _load_sessions()
    sessions.pop(str(user_id), None)
    _save_sessions(sessions)


@Drone.on(events.NewMessage(incoming=True, pattern="/login"))
async def login_cmd(event):
    if not event.is_private:
        return await event.reply("Please use /login in private chat.")

    user_id = event.sender_id

    if get_user_session(user_id):
        return await event.reply(
            "You are already logged in.\n"
            "Use /logout first if you want to switch accounts."
        )

    async with Drone.conversation(event.chat_id, timeout=120) as conv:
        await conv.send_message(
            "**Phone Number Login**\n\n"
            "Send your phone number in international format.\n"
            "Example: `+919876543210`\n\n"
            "Send /cancel to abort."
        )
        try:
            phone_msg = await conv.get_response()
        except asyncio.TimeoutError:
            return await event.respond("Login timed out. Try again with /login.")

        phone = phone_msg.text.strip() if phone_msg.text else ""
        if phone.lower() == "/cancel":
            return await conv.send_message("Login cancelled.")
        if not phone.startswith("+"):
            return await conv.send_message(
                "Invalid format — phone number must start with `+`.\nTry /login again."
            )

        await conv.send_message("Connecting to Telegram...")

        acc = Client(
            f"login_tmp_{user_id}",
            api_id=int(API_ID),
            api_hash=API_HASH,
        )
        try:
            await acc.connect()
        except Exception as e:
            return await conv.send_message(f"Connection error: `{e}`\nTry /login again.")

        try:
            sent_code = await acc.send_code(phone)
        except FloodWait as fw:
            await acc.disconnect()
            val = fw.value if hasattr(fw, 'value') else fw.x
            return await conv.send_message(
                f"Too many requests. Try again after `{val}` seconds."
            )
        except Exception as e:
            await acc.disconnect()
            return await conv.send_message(
                f"Failed to send OTP: `{e}`\n\nCheck your phone number and try /login again."
            )

        await conv.send_message(
            "OTP sent to your Telegram app (or SMS).\n\n"
            "Send the code now — e.g. `12345`\n"
            "You have 2 minutes. Send /cancel to abort."
        )
        try:
            code_msg = await conv.get_response()
        except asyncio.TimeoutError:
            await acc.disconnect()
            return await conv.send_message("Timed out waiting for OTP. Try /login again.")

        code = code_msg.text.strip() if code_msg.text else ""
        if code.lower() == "/cancel":
            await acc.disconnect()
            return await conv.send_message("Login cancelled.")

        try:
            await acc.sign_in(phone, sent_code.phone_code_hash, code)

        except PhoneCodeInvalid:
            await acc.disconnect()
            return await conv.send_message("Invalid OTP code. Try /login again.")

        except PhoneCodeExpired:
            await acc.disconnect()
            return await conv.send_message("OTP expired. Try /login again.")

        except SessionPasswordNeeded:
            await conv.send_message(
                "Two-step verification (2FA) is enabled on your account.\n\n"
                "Send your 2FA password now. Send /cancel to abort."
            )
            try:
                pw_msg = await conv.get_response()
            except asyncio.TimeoutError:
                await acc.disconnect()
                return await conv.send_message("Timed out. Try /login again.")

            password = pw_msg.text.strip() if pw_msg.text else ""
            if password.lower() == "/cancel":
                await acc.disconnect()
                return await conv.send_message("Login cancelled.")

            try:
                await acc.check_password(password)
            except Exception as e:
                await acc.disconnect()
                return await conv.send_message(
                    f"Wrong 2FA password: `{e}`\nTry /login again."
                )

        except Exception as e:
            await acc.disconnect()
            return await conv.send_message(f"Login failed: `{e}`\nTry /login again.")

        try:
            session_string = await acc.export_session_string()
            await acc.disconnect()
        except Exception as e:
            try:
                await acc.disconnect()
            except Exception:
                pass
            return await conv.send_message(
                f"Failed to save session: `{e}`\nTry /login again."
            )

        # Clean up temporary session file created by Pyrogram
        for fname in [f"login_tmp_{user_id}.session", f"login_tmp_{user_id}"]:
            if os.path.exists(fname):
                try:
                    os.remove(fname)
                except Exception:
                    pass

        set_user_session(user_id, session_string)

        await conv.send_message(
            "✅ **Logged in successfully!**\n\n"
            "You can now send any Telegram message link to save it.\n\n"
            "Use /logout to log out."
        )


@Drone.on(events.NewMessage(incoming=True, pattern="/logout"))
async def logout_cmd(event):
    if not event.is_private:
        return await event.reply("Please use /logout in private chat.")

    user_id = event.sender_id
    if not get_user_session(user_id):
        return await event.reply("You are not logged in.")

    clear_user_session(user_id)

    for fname in [f"login_tmp_{user_id}.session", f"user_{user_id}.session",
                  f"login_tmp_{user_id}", f"user_{user_id}"]:
        if os.path.exists(fname):
            try:
                os.remove(fname)
            except Exception:
                pass

    await event.reply("✅ Logged out successfully.")


@Drone.on(events.NewMessage(incoming=True, pattern="/mysession"))
async def mysession_cmd(event):
    if not event.is_private:
        return
    user_id = event.sender_id
    if get_user_session(user_id):
        await event.reply("✅ You are logged in with your personal account.")
    else:
        await event.reply(
            "❌ You are not logged in.\n\n"
            "Use /login to log in with your phone number."
        )
