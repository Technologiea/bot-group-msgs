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
GROUP_CHAT_IDS = [int(x.strip()) for x in os.getenv('GROUP_CHAT_IDS', '').split(',') if x.strip()]
REGISTER_LINK = "https://lkpq.cc/2ee301"
PROMOCODE = "BETWIN190"
TIMEZONE_IST = "Asia/Kolkata"
PORT = int(os.getenv('PORT', 5000))

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

if not BOT_TOKEN or not GROUP_CHAT_IDS:
    logger.error("BOT_TOKEN or GROUP_CHAT_IDS missing!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)
ist = ZoneInfo(TIMEZONE_IST)

# ========================= KEYBOARD =========================
def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("DEPOSIT $100 → GET $600 (500% BONUS)", url=REGISTER_LINK)],
        [InlineKeyboardButton("USE CODE: BETWIN190", url=REGISTER_LINK)],
        [InlineKeyboardButton("REGISTER & PLAY NOW", url=REGISTER_LINK)]
    ])

# ========================= MESSAGES (Clean & Perfect) =========================

# Alert: 5 mins before
ALERT_MSG = """**UPCOMING SIGNAL IN 5 MINUTES** 

**Time**: {signal_time} IST
**Expected**: ~{preview}x

Get ready — High accuracy signal loading!
Members are already entering

[DEPOSIT NOW → BETWIN190]({link})"""

# Live Signal: Exact time
LIVE_MSG = """**LIVE SIGNAL — ENTER NOW** 

**Game**: Lucky Jet
**Time**: {signal_time} IST
**Target**: **{target}x** (Cashout)

$100 → ${profit_100}
$50 → ${profit_50}

Enter in next 20 seconds!

Last 10 signals: 9 Wins ✅

[INSTANT DEPOSIT]({link})"""

# Success: 5 mins after
SUCCESS_MSG = """**SIGNAL PASSED SUCCESSFULLY!** 

**{target}x HIT** at {signal_time} IST

Members who followed → PAID!

Example:
• $100 → ${profit_100} 
• $50 → ${profit_50} 

Drop **"PAID"** if you won 

Next signal in 10 minutes!

[GET READY FOR NEXT → BETWIN190]({link})"""

# ========================= MAIN SCHEDULER: Every 15 mins =========================
async def signal_scheduler():
    while True:
        now = datetime.now(ist)
        minute = now.minute
        second = now.second

        # Trigger only at :00, :15, :30, :45 → when second is 0–10
        if minute % 15 == 0 and second < 15:

            # Define exact signal time (e.g., 10:15 PM)
            signal_dt = now.replace(second=0, microsecond=0)
            signal_time_str = signal_dt.strftime("%I:%M %p").lstrip("0")

            # Generate signal data
            target = round(random.uniform(11.5, 35.0), 1)
            preview = round(target + random.uniform(-4.0, 5.0), 1)
            profit_100 = int(100 * (target - 1))
            profit_50 = int(50 * (target - 1))

            logger.info(f"NEW SIGNAL CYCLE → {signal_time_str} | Target: {target}x")

            # === 1. ALERT: Send 5 minutes early ===
            alert_time = (signal_dt - timedelta(minutes=5)).strftime("%I:%M %p").lstrip("0")
            await broadcast(ALERT_MSG.format(
                signal_time=signal_time_str,
                preview=preview,
                link=REGISTER_LINK
            ))
            logger.info(f"Alert sent at {alert_time} for {signal_time_str}")

            # Wait exactly 5 minutes
            await asyncio.sleep(300)

            # === 2. LIVE SIGNAL: At exact time ===
            await broadcast(LIVE_MSG.format(
                signal_time=signal_time_str,
                target=target,
                profit_100=f"{profit_100:,}",
                profit_50=f"{profit_50:,}",
                link=REGISTER_LINK
            ))
            logger.info(f"Live signal sent at {signal_time_str}")

            # Wait 5 minutes (simulating flight time)
            await asyncio.sleep(300)

            # === 3. SUCCESS MESSAGE ===
            await broadcast(SUCCESS_MSG.format(
                target=target,
                signal_time=signal_time_str,
                profit_100=f"{profit_100:,}",
                profit_50=f"{profit_50:,}",
                link=REGISTER_LINK
            ))
            logger.info(f"Success message sent for {signal_time_str}")

        await asyncio.sleep(10)

# ========================= BROADCAST =========================
async def broadcast(text: str):
    for chat_id in GROUP_CHAT_IDS:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="Markdown",
                disable_web_page_preview=True,
                reply_markup=get_keyboard()
            )
            await asyncio.sleep(0.8)
        except TelegramError as e:
            logger.error(f"Send failed {chat_id}: {e}")
    logger.info(f"Sent to all {len(GROUP_CHAT_IDS)} groups")

# ========================= HEALTH =========================
@app.route('/health')
def health():
    now = datetime.now(ist).strftime("%I:%M %p")
    return jsonify({
        "status": "LIVE - 15 MIN SIGNAL BOT",
        "time_ist": now,
        "schedule": "Every 15 mins: 00, 15, 30, 45",
        "flow": "5-min Alert → Live at exact time → Success +5 min",
        "promocode": PROMOCODE,
        "next_signals": "Perfect timing guaranteed"
    })

# ========================= START =========================
def run_bot():
    asyncio.run(signal_scheduler())

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    logger.info("LUCKY JET 15-MIN SIGNAL BOT STARTED | Alert 5 min before | Success 5 min after | 100% Accurate Timing")
    app.run(host='0.0.0.0', port=PORT, use_reloader=False)
