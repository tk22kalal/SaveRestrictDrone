#Github.com/Vasusen-code

import asyncio
import os
import time
from io import BytesIO

from .. import bot as Drone
from telethon import events

S = '/' + 's' + 'p' + 'e' + 'e' + 'd' + 't' + 'e' + 's' + 't'

@Drone.on(events.NewMessage(incoming=True, pattern=f"{S}"))
async def speedtest(event):
    """Test upload and download speed of the bot"""
    
    msg = await event.reply("Starting speedtest...")
    
    try:
        # Test file size - 5MB
        test_size = 5 * 1024 * 1024
        test_data = os.urandom(test_size)
        
        # Download speed test (upload a file to Telegram and measure time)
        upload_start = time.time()
        
        # Create a temporary file for upload
        temp_file = 'speedtest_temp.bin'
        with open(temp_file, 'wb') as f:
            f.write(test_data)
        
        # Upload file
        try:
            upload_msg = await event.client.send_file(
                event.chat_id,
                temp_file,
                caption="Speedtest Upload"
            )
        except Exception as e:
            await msg.edit(f"Upload test failed: {str(e)}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return
        
        upload_end = time.time()
        upload_time = upload_end - upload_start
        
        # Delete the uploaded file
        try:
            await upload_msg.delete()
        except:
            pass
        
        # Download speed test (download the file we just uploaded)
        download_start = time.time()
        
        try:
            downloaded_file = await event.client.download_media(upload_msg)
        except Exception as e:
            # If download fails, calculate based on upload time
            downloaded_file = temp_file
        
        download_end = time.time()
        download_time = download_end - download_start
        
        # Calculate speeds in Mbps
        upload_speed = (test_size / (1024 * 1024)) / upload_time if upload_time > 0 else 0
        download_speed = (test_size / (1024 * 1024)) / download_time if download_time > 0 else 0
        
        # Format results
        result_text = (
            "🚀 **SPEEDTEST RESULTS** 🚀\n\n"
            f"📤 **Upload Speed:** `{upload_speed:.2f} Mbps`\n"
            f"📥 **Download Speed:** `{download_speed:.2f} Mbps`\n\n"
            f"⏱️ **Upload Time:** `{upload_time:.2f}s`\n"
            f"⏱️ **Download Time:** `{download_time:.2f}s`\n"
            f"📦 **Test File Size:** `5 MB`"
        )
        
        await msg.edit(result_text)
        
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)
        if downloaded_file and os.path.exists(downloaded_file):
            os.remove(downloaded_file)
            
    except Exception as e:
        await msg.edit(f"❌ Speedtest failed: {str(e)}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
