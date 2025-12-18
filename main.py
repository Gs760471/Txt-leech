# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os
import re
import sys
import time
import asyncio
import requests
import utkarshwofree

import core as helper
from utils import progress_bar
from vars import API_ID, API_HASH, BOT_TOKEN

from aiohttp import ClientSession
from pyromod import listen
from subprocess import getstatusoutput

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait

# ================= BOT INIT =================

bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ================= START =================

@bot.on_message(filters.command("start"))
async def start(bot: Client, m: Message):
    await m.reply_text(
        f"<b>Hello {m.from_user.mention} 👋\n\n"
        f"📌 Commands:\n"
        f"/run – Extract Utkarsh batch links\n"
        f"/upload – Upload txt & download content\n"
        f"/stop – Restart bot</b>"
    )

# ================= STOP =================

@bot.on_message(filters.command("stop"))
async def stop(bot: Client, m: Message):
    await m.reply_text("**Stopped 🚦 Restarting...**")
    os.execl(sys.executable, sys.executable, *sys.argv)

# =========================================================
# ===================== RUN UTKARSH ========================
# =========================================================

@bot.on_message(filters.command("run"))
async def run_utkarsh(bot: Client, m: Message):
    try:
        # ---- LOGIN ----
        q1 = await m.reply_text("🔐 **Enter Login ID / Mobile / Email:**")
        r1 = await bot.listen(m.chat.id)
        email = r1.text.strip()
        await r1.delete()
        await q1.delete()

        # ---- PASSWORD ----
        q2 = await m.reply_text("🔑 **Enter Password:**")
        r2 = await bot.listen(m.chat.id)
        password = r2.text.strip()
        await r2.delete()
        await q2.delete()

        # ---- BATCH ID ----
        q3 = await m.reply_text("📦 **Enter Batch ID:**")
        r3 = await bot.listen(m.chat.id)
        batch_id = r3.text.strip()
        await r3.delete()
        await q3.delete()

        status = await m.reply_text("⏳ **Running script, please wait...**")

        # ---- RUN SCRIPT IN THREAD ----
        loop = asyncio.get_event_loop()
        files = await loop.run_in_executor(
            None,
            utkarshwofree.run_script,
            email,
            password,
            batch_id
        )

        if not files:
            await status.edit("❌ **No files generated**")
            return

        await status.edit("📤 **Uploading files...**")

        for f in files:
            if os.path.exists(f):
                await bot.send_document(m.chat.id, f)
                os.remove(f)

        await status.edit("✅ **Done Successfully!**")

        # security cleanup
        del password

    except Exception as e:
        await m.reply_text(f"❌ **Error:** `{e}`")

# =========================================================
# ===================== UPLOAD TXT =========================
# =========================================================

@bot.on_message(filters.command("upload"))
async def upload(bot: Client, m: Message):
    editable = await m.reply_text("📄 **Send TXT file**")
    input_file: Message = await bot.listen(editable.chat.id)
    file_path = await input_file.download()
    await input_file.delete()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().splitlines()
        os.remove(file_path)
    except Exception:
        await editable.edit("❌ **Invalid file**")
        return

    links = [i.split("://", 1) for i in content if "://" in i]

    await editable.edit(
        f"🔗 **Total Links Found:** `{len(links)}`\n\n"
        f"Send starting index (default = 1)"
    )

    start_msg = await bot.listen(m.chat.id)
    start = int(start_msg.text) if start_msg.text.isdigit() else 1
    await start_msg.delete()

    await editable.edit("📦 **Send Batch Name**")
    batch_msg = await bot.listen(m.chat.id)
    batch_name = batch_msg.text
    await batch_msg.delete()

    await editable.edit("📸 **Choose Resolution (144/240/360/480/720/1080)**")
    res_msg = await bot.listen(m.chat.id)
    quality = res_msg.text
    await res_msg.delete()

    await editable.edit("📝 **Send Caption**")
    cap_msg = await bot.listen(m.chat.id)
    caption = cap_msg.text
    await cap_msg.delete()

    await editable.edit(
        "🖼 **Send Thumbnail URL or `no`**"
    )
    thumb_msg = await bot.listen(m.chat.id)
    thumb = thumb_msg.text
    await thumb_msg.delete()
    await editable.delete()

    if thumb.startswith("http"):
        getstatusoutput(f"wget '{thumb}' -O thumb.jpg")
        thumb = "thumb.jpg"
    else:
        thumb = None

    count = start

    for i in range(start - 1, len(links)):
        try:
            name = f"{str(count).zfill(3)}) {links[i][0][:60]}"
            url = "https://" + links[i][1]

            show = await m.reply_text(
                f"⬇️ **Downloading**\n\n"
                f"🎬 `{name}`\n"
                f"📺 `{quality}p`"
            )

            cmd = f'yt-dlp -f "b[height<={quality}]" "{url}" -o "{name}.mp4"'
            file = await helper.download_video(url, cmd, name)

            await show.delete()
            await helper.send_vid(
                bot, m, caption, file, thumb, name, show
            )

            os.remove(file)
            count += 1
            time.sleep(1)

        except FloodWait as e:
            await asyncio.sleep(e.x)
        except Exception as e:
            await m.reply_text(f"❌ Error: {e}")
            continue

    await m.reply_text("✅ **Upload Completed**")

# ================= RUN BOT =================

bot.run()
