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
# In Render, add GROUP_CHAT_IDS as a comma-separated list of numbers
GROUP_CHAT_IDS = [int(x.strip()) for x in os.getenv('GROUP_CHAT_IDS', '').split(',') if x.strip()]
REGISTER_LINK = "https://lkpq.cc/22fba15d"
PROMOCODE = "BETWIN190"
TIMEZONE_IST = "Asia/Kolkata"
PORT = int(os.getenv('PORT', 10000)) 

# The APK file must be in the same folder as this script on GitHub
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

# ========================= CONVERSION MESSAGES =========================

APK_CAPTION = f"""📥 **OFFICIAL AVIATOR APP DETECTED** 📥

Using the app reduces signal lag and increases winning speed!

1️⃣ **Download** the APK file below.
2️⃣ **Login/Register** with code: `{PROMOCODE}`
3️⃣ **Deposit** at least ₹500 to activate the 500% bonus.

⚡ *App users get signals 2 seconds faster than web users!*"""

ALERT_MSG = """⚠️ **SIGNAL SCANNING STARTED...** ⚠️

⏰ **Target Time:** {signal_time} IST
🎯 **Expected Multiplier:** Over {preview}x

✅ Status: **Algorithm Synchronized**
💎 Use Promo Code: `{promocode}`

*Check your balance now. If it's low, deposit quickly to avoid missing the flight!* 🛫"""

LIVE_MSG = """🔔 **LIVE SIGNAL - BET NOW!** 🔔

🎮 **Game:** AVIATOR
⏰ **Time:** {signal_time} IST
🎯 **AUTO-CASHOUT AT:** **{target}x**

💰 **ESTIMATED WINNINGS:**
• Deposit ₹500  ➡️  **₹{profit_500}**
• Deposit ₹1,000 ➡️  **₹{profit_1000}**
• Deposit ₹5,000 ➡️  **₹{profit_5000}**

⏳ **Action:** Open App, place bet, and cashout at {target}x!"""

SUCCESS_MSG = """✅ **PROFIT CONFIRMED! {target}x SMASHED!!** ✅

Signal Time: {signal_time} IST
Our prediction hit perfectly! 🚀

📊 **EARNINGS LIST:**
• User A: ₹500  ➡️  **₹{profit_500} WIN**
• User B: ₹1,000 ➡️  **₹{profit_1000} WIN**

Congratulations! Send your winning screenshots to the admin! 💸💸"""

# ========================= CORE FUNCTIONS =========================

async def send_apk_to_all():
    """Sends the actual APK file to the groups"""
    if not os.path.exists(APK_FILE_NAME):
        logger.error(f"FILE MISSING: {APK_FILE_NAME} not found in root directory!")
        return

    for chat_id in GROUP_CHAT_IDS:
        try:
            with open(APK_FILE_NAME, 'rb') as doc:
                await bot.send_document(
                    chat_id=chat_id,
                    document=InputFile(doc, filename="1Win_Aviator_Official.apk"),
                    caption=APK_CAPTION,
                    parse_mode="Markdown",
                    reply_markup=get_main_keyboard()
                )
            logger.info(f"APK delivered to {chat_id}")
        except Exception as e:
            logger.error(f"APK delivery failed for {chat_id}: {e}")

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
            logger.error(f"Broadcast error: {e}")

# ========================= SCHEDULER =========================

async def signal_scheduler():
    # Send APK immediately when the server starts
    await send_apk_to_all()
    
    while True:
        now = datetime.now(ist)
        # Active: 10:00 PM to 01:00 AM IST
        is_active = now.hour >= 22 or now.hour < 1
        
        if not is_active:
            await asyncio.sleep(60)
            continue

        # Get next 15-min mark
        next_15 = ((now.minute // 15) + 1) * 15
        if next_15 == 60:
            signal_dt = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        else:
            signal_dt = now.replace(minute=next_15, second=0, microsecond=0)
            
        alert_dt = signal_dt - timedelta(minutes=5)
        
        # If we are in the "Alert Window" (5 mins before signal)
        time_diff = (alert_dt - now).total_seconds()
        if 0 <= time_diff < 30:
            target = round(random.uniform(2.2, 4.9), 2)
            preview = round(target - 0.3, 1)
            
            # 1. ALERT
            await broadcast(ALERT_MSG.format(
                signal_time=signal_dt.strftime("%I:%M %p"),
                preview=preview,
                promocode=PROMOCODE
            ), get_main_keyboard())
            
            # Wait for signal time
            wait_live = (signal_dt - datetime.now(ist)).total_seconds()
            if wait_live > 0:
                await asyncio.sleep(wait_live)
            
            # 2. LIVE
            p500, p1000, p5000 = int(500 * target), int(1000 * target), int(5000 * target)
            await broadcast(LIVE_MSG.format(
                signal_time=signal_dt.strftime("%I:%M %p"),
                target=target,
                profit_500=f"{p500:,}",
                profit_1000=f"{p1000:,}",
                profit_5000=f"{p5000:,}"
            ), get_main_keyboard())

            # 3. SUCCESS (2 minutes after signal)
            await asyncio.sleep(120)
            await broadcast(SUCCESS_MSG.format(
                target=target,
                signal_time=signal_dt.strftime("%I:%M %p"),
                profit_500=f"{p500:,}",
                profit_1000=f"{p1000:,}"
            ), get_main_keyboard())

        await asyncio.sleep(25)

# ========================= DEPLOYMENT =========================

@app.route('/')
def health():
    return "Aviator Bot Live", 200

def run_async():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(signal_scheduler())

if __name__ == "__main__":
    # Start the background scheduler
    threading.Thread(target=run_async, daemon=True).start()
    # Start the Flask server for Render
    app.run(host='0.0.0.0', port=PORT)
