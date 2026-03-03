import asyncio
import random
import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import TelegramError
from flask import Flask, jsonify
import threading

# ========================= CONFIG =========================
BOT_TOKEN = os.getenv('BOT_TOKEN')
# Use a comma-separated list of IDs in your Environment Variables
GROUP_CHAT_IDS = [int(x.strip()) for x in os.getenv('GROUP_CHAT_IDS', '').split(',') if x.strip()]
REGISTER_LINK = "https://lkpq.cc/2551"
PROMOCODE = "BETWIN190"
TIMEZONE_IST = "Asia/Kolkata"
PORT = int(os.getenv('PORT', 5000))

# Daily operation hours (22:00 to 01:00 IST)
ACTIVE_HOURS_START = 22  
ACTIVE_HOURS_END = 1     

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)
ist = ZoneInfo(TIMEZONE_IST)

# ========================= KEYBOARDS =========================
def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 REGISTER & GET 500% BONUS", url=REGISTER_LINK)],
        [InlineKeyboardButton("📱 OPEN AVIATOR GAME", url=REGISTER_LINK)]
    ])

# ========================= MESSAGES (INR VERSION) =========================

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

⏳ **Action:** Place bet and cashout at {target}x exactly!

**Promo Code:** `{promocode}`"""

SUCCESS_MSG = """✅ **PROFIT BOOKED! {target}x HIT!!** ✅

The algorithm predicted {target}x and we smashed it at {signal_time} IST! 🚀

📊 **RESULTS:**
• ₹500  ➡️  **₹{profit_500} WIN**
• ₹1,000 ➡️  **₹{profit_1000} WIN**

Congratulations to everyone who followed! 💸💸
👇 Send your winning screenshots to admin!

**Next signal coming soon...**"""

# ========================= LOGIC & SCHEDULER =========================

def get_next_signal_time(now: datetime):
    current_minute = now.minute
    next_15 = ((current_minute // 15) + 1) * 15
    
    if next_15 == 60:
        signal_dt = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        signal_dt = now.replace(minute=next_15, second=0, microsecond=0)
    
    alert_dt = signal_dt - timedelta(minutes=5)
    return signal_dt, alert_dt

async def signal_scheduler():
    while True:
        now = datetime.now(ist)
        
        # Check active hours
        hour = now.hour
        is_active = hour >= ACTIVE_HOURS_START or hour < ACTIVE_HOURS_END
        
        if not is_active:
            await asyncio.sleep(60)
            continue

        signal_dt, alert_dt = get_next_signal_time(now)
        
        # 1. ALERT PHASE
        time_to_alert = (alert_dt - now).total_seconds()
        if 0 <= time_to_alert < 30:
            target = round(random.uniform(2.0, 5.5), 2)
            preview = round(target - 0.4, 1)
            
            await broadcast(ALERT_MSG.format(
                signal_time=signal_dt.strftime("%I:%M %p"),
                preview=preview,
                promocode=PROMOCODE
            ), get_main_keyboard())
            
            # Wait for Live
            await asyncio.sleep((signal_dt - datetime.now(ist)).total_seconds())
            
            # 2. LIVE PHASE
            p500 = int(500 * target)
            p1000 = int(1000 * target)
            p5000 = int(5000 * target)

            await broadcast(LIVE_MSG.format(
                signal_time=signal_dt.strftime("%I:%M %p"),
                target=target,
                profit_500=f"{p500:,}",
                profit_1000=f"{p1000:,}",
                profit_5000=f"{p5000:,}",
                promocode=PROMOCODE
            ), get_main_keyboard())

            # 3. SUCCESS PHASE (3 mins later)
            await asyncio.sleep(180)
            await broadcast(SUCCESS_MSG.format(
                target=target,
                signal_time=signal_dt.strftime("%I:%M %p"),
                profit_500=f"{p500:,}",
                profit_1000=f"{p1000:,}",
                promocode=PROMOCODE
            ), get_main_keyboard())

        await asyncio.sleep(20)

async def broadcast(message, keyboard):
    for chat_id in GROUP_CHAT_IDS:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error: {e}")

# Flask Health Check
@app.route('/')
def home(): return "Bot is Alive"

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(signal_scheduler())

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
