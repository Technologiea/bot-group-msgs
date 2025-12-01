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
CURRENCY_SYMBOL = "₹"  # Changed to INR feel (or keep $ if needed)
PORT = int(os.getenv('PORT', 5000))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
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
        [InlineKeyboardButton("🚀 DEPOSIT $100 → GET $600 (500% BONUS)", url=REGISTER_LINK)],
        [InlineKeyboardButton("🔥 USE CODE: BETWIN190 FOR BONUS", url=REGISTER_LINK)],
        [InlineKeyboardButton("✅ REGISTER & PLAY NOW", url=REGISTER_LINK)]
    ])

# ========================= MESSAGES (Clean & Clear) =========================

# 5 Minutes Before → Alert
ALERT_TEMPLATE = """🚨 **UPCOMING BIG SIGNAL IN 5 MINUTES** 🚨

🕐 **Time**: {time} IST
📊 **Expected Target**: ~{preview}x

🔥 Get ready! High win probability detected
💰 Many members already placing bets

Prepare your balance now → Next rocket is loading!

[⚡ DEPOSIT & GET 500% BONUS → BETWIN190]({link})"""

# At Exact Time → Live Signal
LIVE_TEMPLATE = """✅ **LIVE SIGNAL — ENTER NOW** ✅

🎮 **Game**: Lucky Jet
🕐 **Time**: {time} IST
🎯 **Cashout Target**: **{target}x**

💰 $100 → ${profit}
💰 $50 → ${half_profit}

⏰ **Enter within 20 seconds!**

Accuracy Last 10: 9/10 Wins ✅

[🚀 DEPOSIT INSTANTLY → BETWIN190]({link})"""

# After Signal Hits → Success
SUCCESS_TEMPLATE = """🎉 **SIGNAL PASSED SUCCESSFULLY!** 🎉

✅ **{target}x HIT CONFIRMED** at {time} IST
💰 **Members who followed → PAID BIG!**

🏆 Example Profits:
   • $100 → ${profit}
   • $50 → ${half_profit}

Type **"PAID"** if you won! 🔥

Next signal in ~40 minutes. Stay ready!

[💸 NEXT SIGNAL → KEEP BONUS ACTIVE]({link})"""

# ========================= SCHEDULER: Every 40 mins (10:00 PM to 1:00 AM IST) =========================
async def send_signal_cycle():
    while True:
        now = datetime.now(ist)
        current_time = now.strftime("%H:%M")
        current_minute = now.minute

        # Run only between 10:00 PM to 1:00 AM IST
        if (22 <= now.hour < 25) or (now.hour == 1 and now.minute < 20):
            # Trigger every 40 minutes: at :00 and :40
            if current_minute in [0, 40] and 0 <= now.second < 15:

                signal_time = now.strftime("%I:%M %p").lstrip("0")
                alert_time_dt = now - timedelta(minutes=5)
                alert_time = alert_time_dt.strftime("%I:%M %p").lstrip("0")

                # Random realistic data
                target = round(random.uniform(12.0, 32.0), 1)
                preview = round(target + random.uniform(-3.5, 4.5), 1)
                profit_100 = int(100 * (target - 1))
                profit_50 = int(50 * (target - 1))

                logger.info(f"🚀 Sending Signal at {signal_time} IST | Target: {target}x")

                # === 1. ALERT: 5 minutes before ===
                await broadcast(ALERT_TEMPLATE.format(
                    time=alert_time,
                    preview=preview,
                    link=REGISTER_LINK
                ))
                logger.info("Alert sent (5 min before)")

                # Wait exactly 5 minutes
                await asyncio.sleep(300)  # 5 minutes

                # === 2. LIVE SIGNAL: At exact time ===
                await broadcast(LIVE_TEMPLATE.format(
                    time=signal_time,
                    target=target,
                    profit=f"{profit_100:,}",
                    half_profit=f"{profit_50:,}",
                    link=REGISTER_LINK
                ))
                logger.info("Live signal sent")

                # Wait 3 minutes (signal "hits")
                await asyncio.sleep(180)

                # === 3. SUCCESS MESSAGE ===
                await broadcast(SUCCESS_TEMPLATE.format(
                    target=target,
                    time=signal_time,
                    profit=f"{profit_100:,}",
                    half_profit=f"{profit_50:,}",
                    link=REGISTER_LINK
                ))
                logger.info("Success message sent")

                # Optional: Bonus reminder after 15 mins (uncomment if needed)
                # await asyncio.sleep(900)
                # await broadcast(random.choice(GUIDE_MSGS).format(link=REGISTER_LINK))

        await asyncio.sleep(10)

# ========================= BROADCAST FUNCTION =========================
async def broadcast(text: str):
    sent = 0
    for chat_id in GROUP_CHAT_IDS:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="Markdown",
                disable_web_page_preview=True,
                reply_markup=get_keyboard()
            )
            sent += 1
            await asyncio.sleep(0.8)
        except TelegramError as e:
            logger.error(f"Failed to send to {chat_id}: {e}")
    logger.info(f"Message sent to {sent}/{len(GROUP_CHAT_IDS)} groups")

# ========================= HEALTH CHECK =========================
@app.route('/health')
def health():
    now_ist = datetime.now(ist).strftime("%I:%M %p")
    return jsonify({
        "status": "RUNNING - Lucky Jet Signal Bot",
        "time_ist": now_ist,
        "schedule": "10:00 PM – 1:00 AM IST",
        "frequency": "Every 40 minutes (at :00 & :40)",
        "next_signal": "5-min alert → Exact time → Success message",
        "promocode": PROMOCODE
    })

# ========================= START BOT =========================
def run_bot():
    asyncio.run(send_signal_cycle())

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    logger.info("🚀 LUCKY JET SIGNAL BOT STARTED | Clean Mode | 5-Min Alert → Live → Success | IST Time")
    app.run(host='0.0.0.0', port=PORT, use_reloader=False)
