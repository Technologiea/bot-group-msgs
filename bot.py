import asyncio
import random
import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from telegram.error import TelegramError
from flask import Flask
import threading

# ========================= CONFIG =========================
BOT_TOKEN = os.getenv('BOT_TOKEN')
# Comma-separated IDs in Render Env Vars
GROUP_CHAT_IDS = [int(x.strip()) for x in os.getenv('GROUP_CHAT_IDS', '').split(',') if x.strip()]
REGISTER_LINK = "https://lkpq.cc/22fba15d"
PROMOCODE = "BETWIN190"
TIMEZONE_IST = "Asia/Kolkata"
PORT = int(os.getenv('PORT', 10000)) # Render uses 10000 by default

# Ensure this exact file is in your GitHub repo root
APK_FILE_NAME = "1win .apk" 

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)
ist = ZoneInfo(TIMEZONE_IST)

# ========================= KEYBOARDS =========================
def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 REGISTER & GET 500% BONUS", url=REGISTER_LINK)],
        [InlineKeyboardButton("💳 DEPOSIT NOW (INSTANT)", url=REGISTER_LINK)],
        [InlineKeyboardButton("📱 DOWNLOAD APP", url=REGISTER_LINK)]
    ])

# ========================= MESSAGES =========================

APK_CAPTION = f"""📥 **INSTALL THE OFFICIAL 1WIN APP** 📥

For the fastest signals and zero lag, use the Android App!

1️⃣ **Download** the APK attached below.
2️⃣ **Register** using code: `{PROMOCODE}`
3️⃣ **Deposit** to get **500% Bonus** (₹1000 becomes ₹5000).

⚠️ *Web version has 2s delay. Use the APP to win!*"""

ALERT_MSG = """⚠️ **PREPARING NEXT SIGNAL...** ⚠️

⏰ **Time:** {signal_time} IST
🎯 **Expectation:** Over {preview}x

✅ Status: **Analyzing Algorithm...**
💎 Use Code: `{promocode}`

*Make sure your balance is ready! Don't miss this flight.* 🛫"""

LIVE_MSG = """🔔 **LIVE SIGNAL - BET NOW!** 🔔

🎮 **Game:** AVIATOR
⏰ **Time:** {signal_time} IST
🎯 **Auto-Cashout:** **{target}x**

💰 **ESTIMATED PROFIT:**
• ₹500  ➡️  **₹{profit_500}**
• ₹1,000 ➡️  **₹{profit_1000}**
• ₹5,000 ➡️  **₹{profit_5000}**

⏳ **Action:** Place bet and cashout at {target}x exactly!"""

SUCCESS_MSG = """✅ **PROFIT BOOKED! {target}x HIT!!** ✅

The algorithm predicted {target}x and we smashed it at {signal_time} IST! 🚀

📊 **RESULTS:**
• ₹500  ➡️  **₹{profit_500} WIN**
• ₹1,000 ➡️  **₹{profit_1000} WIN**

Congratulations to everyone who followed! 💸💸"""

# ========================= BROADCAST LOGIC =========================

async def send_apk_to_all():
    """Broadcasts the APK file to all configured groups"""
    if not os.path.exists(APK_FILE_NAME):
        logger.error(f"CRITICAL: {APK_FILE_NAME} not found in root directory!")
        return

    for chat_id in GROUP_CHAT_IDS:
        try:
            with open(APK_FILE_NAME, 'rb') as doc:
                await bot.send_document(
                    chat_id=chat_id,
                    document=InputFile(doc, filename="1Win_Official_App.apk"),
                    caption=APK_CAPTION,
                    parse_mode="Markdown",
                    reply_markup=get_main_keyboard()
                )
            logger.info(f"APK successfully sent to {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send APK to {chat_id}: {e}")

async def broadcast(message, keyboard):
    for chat_id in GROUP_CHAT_IDS:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Broadcast error for {chat_id}: {e}")

# ========================= SCHEDULER =========================

async def signal_scheduler():
    # Initial APK send when server starts
    await send_apk_to_all()
    
    while True:
        now = datetime.now(ist)
        hour = now.hour
        
        # Active hours: 10 PM to 1 AM IST
        is_active = hour >= 22 or hour < 1
        
        if not is_active:
            await asyncio.sleep(60)
            continue

        # Logic to find the next 15-minute interval
        current_minute = now.minute
        next_15 = ((current_minute // 15) + 1) * 15
        if next_15 == 60:
            signal_dt = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        else:
            signal_dt = now.replace(minute=next_15, second=0, microsecond=0)
            
        alert_dt = signal_dt - timedelta(minutes=5)
        time_until_alert = (alert_dt - now).total_seconds()
        
        if 0 <= time_until_alert < 30:
            target = round(random.uniform(2.1, 4.8), 2)
            preview = round(target - 0.3, 1)
            
            # Phase 1: ALERT
            await broadcast(ALERT_MSG.format(
                signal_time=signal_dt.strftime("%I:%M %p"),
                preview=preview,
                promocode=PROMOCODE
            ), get_main_keyboard())
            
            # Wait until the actual signal time
            wait_for_live = (signal_dt - datetime.now(ist)).total_seconds()
            if wait_for_live > 0:
                await asyncio.sleep(wait_for_live)
            
            # Phase 2: LIVE
            p500, p1000, p5000 = int(500 * target), int(1000 * target), int(5000 * target)
            await broadcast(LIVE_MSG.format(
                signal_time=signal_dt.strftime("%I:%M %p"),
                target=target,
                profit_500=f"{p500:,}",
                profit_1000=f"{p1000:,}",
                profit_5000=f"{p5000:,}"
            ), get_main_keyboard())

            # Phase 3: SUCCESS (Post results 2 mins later)
            await asyncio.sleep(120)
            await broadcast(SUCCESS_MSG.format(
                target=target,
                signal_time=signal_dt.strftime("%I:%M %p"),
                profit_500=f"{p500:,}",
                profit_1000=f"{p1000:,}"
            ), get_main_keyboard())

        await asyncio.sleep(30)

# ========================= RUNNER =========================

@app.route('/')
def health_check():
    return "Bot is running on Render", 200

def start_async_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(signal_scheduler())

if __name__ == "__main__":
    # Run the Telegram logic in a background thread
    threading.Thread(target=start_async_loop, daemon=True).start()
    # Run Flask on the port provided by Render
    app.run(host='0.0.0.0', port=PORT)
