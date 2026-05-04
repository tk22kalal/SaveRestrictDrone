#Github.com/Vasusen-code

import asyncio
import os
import time
from io import BytesIO

from .. import bot as Drone
from telethon import events

S = "/" + "s" + "p" + "e" + "e" + "d" + "t" + "e" + "s" + "t"


@Drone.on(events.NewMessage(incoming=True, pattern=f"{S}"))
async def speedtest(event):
    """Test upload and download speed of the bot (5 MB file)."""

    msg = await event.reply("🚀 **Speed Test Starting...**\n\nGenerating 5 MB test file...")

    test_size = 5 * 1024 * 1024  # 5 MB
    temp_file = f"speedtest_{event.sender_id}.bin"
    downloaded_file = None

    try:
        # Write random bytes to disk
        with open(temp_file, "wb") as f:
            f.write(os.urandom(test_size))

        # --- Upload test ---
        await msg.edit("🚀 **Running Speed Test...**\n\n📤 Testing upload speed...")
        up_start = time.time()
        try:
            upload_msg = await event.client.send_file(
                event.chat_id,
                temp_file,
                caption="⚡ Speed test file (5 MB) — will be deleted automatically",
            )
        except Exception as e:
            await msg.edit(f"❌ Upload test failed: `{e}`")
            return

        up_elapsed = time.time() - up_start
        up_speed_mb = (test_size / (1024 * 1024)) / up_elapsed if up_elapsed > 0 else 0

        # --- Download test (before deleting the message!) ---
        await msg.edit("🚀 **Running Speed Test...**\n\n📥 Testing download speed...")
        down_start = time.time()
        try:
            downloaded_file = await event.client.download_media(upload_msg)
        except Exception as e:
            await msg.edit(f"❌ Download test failed: `{e}`")
            return

        down_elapsed = time.time() - down_start
        down_speed_mb = (test_size / (1024 * 1024)) / down_elapsed if down_elapsed > 0 else 0

        # Clean up the uploaded message now that we're done with it
        try:
            await upload_msg.delete()
        except Exception:
            pass

        result = (
            "🚀 **SPEEDTEST RESULTS**\n\n"
            f"📁 **File Size:** `5 MB`\n\n"
            f"📤 **Upload Speed:** `{up_speed_mb:.2f} MB/s`\n"
            f"   ⏱ Time: `{up_elapsed:.2f}s`\n\n"
            f"📥 **Download Speed:** `{down_speed_mb:.2f} MB/s`\n"
            f"   ⏱ Time: `{down_elapsed:.2f}s`"
        )
        await msg.edit(result)

    except Exception as e:
        await msg.edit(f"❌ Speedtest failed: `{e}`")
    finally:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass
        if downloaded_file and os.path.exists(downloaded_file):
            try:
                os.remove(downloaded_file)
            except Exception:
                pass
