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

# Alert: 5 mins after current signal
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

# Success: 5 mins after live signal
SUCCESS_MSG = """**SIGNAL PASSED SUCCESSFULLY!** 

**{target}x HIT** at {signal_time} IST

Members who followed → PAID!

Example:
• $100 → ${profit_100} 
• $50 → ${profit_50} 

Drop **"PAID"** if you won 

Next signal in 10 minutes!

[GET READY FOR NEXT → BETWIN190]({link})"""

# ========================= TIMING CALCULATION =========================
def get_next_signal_time(now: datetime) -> tuple:
    """
    Calculate next signal time and alert time correctly.
    Returns: (signal_dt, alert_dt, next_signal_dt)
    """
    current_minute = now.minute
    
    # Find next 15-minute interval
    next_15 = ((current_minute // 15) + 1) * 15
    if next_15 == 60:
        # Next hour
        signal_dt = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        signal_dt = now.replace(minute=next_15, second=0, microsecond=0)
    
    # Alert is 5 minutes before next signal
    alert_dt = signal_dt - timedelta(minutes=5)
    
    # Calculate the signal after next (for success message timing)
    next_next_15 = next_15 + 15
    if next_next_15 >= 60:
        next_signal_dt = signal_dt.replace(minute=0) + timedelta(hours=1)
    else:
        next_signal_dt = signal_dt.replace(minute=next_next_15)
    
    return signal_dt, alert_dt, next_signal_dt

# ========================= MAIN SCHEDULER =========================
async def signal_scheduler():
    while True:
        now = datetime.now(ist)
        current_time_str = now.strftime("%I:%M:%S %p").lstrip("0")
        
        # Calculate next signal times
        signal_dt, alert_dt, next_signal_dt = get_next_signal_time(now)
        signal_time_str = signal_dt.strftime("%I:%M %p").lstrip("0")
        alert_time_str = alert_dt.strftime("%I:%M %p").lstrip("0")
        
        # Check if it's time to send alert (5 mins before next signal)
        time_to_alert = (alert_dt - now).total_seconds()
        
        if 0 <= time_to_alert < 60:  # Within next minute
            logger.info(f"ALERT TIME DETECTED → Current: {current_time_str}, Alert at: {alert_time_str}, Signal at: {signal_time_str}")
            
            # Generate signal data
            target = round(random.uniform(11.5, 35.0), 1)
            preview = round(target + random.uniform(-4.0, 5.0), 1)
            
            # === 1. SEND ALERT ===
            await broadcast(ALERT_MSG.format(
                signal_time=signal_time_str,
                preview=preview,
                link=REGISTER_LINK
            ))
            logger.info(f"✅ Alert sent for {signal_time_str} signal (Target: {target}x)")
            
            # Wait until exact signal time
            wait_seconds = (signal_dt - now).total_seconds()
            if wait_seconds > 0:
                logger.info(f"⏳ Waiting {int(wait_seconds)}s for live signal at {signal_time_str}")
                await asyncio.sleep(wait_seconds)
            
            # === 2. SEND LIVE SIGNAL ===
            profit_100 = int(100 * (target - 1))
            profit_50 = int(50 * (target - 1))
            
            await broadcast(LIVE_MSG.format(
                signal_time=signal_time_str,
                target=target,
                profit_100=f"{profit_100:,}",
                profit_50=f"{profit_50:,}",
                link=REGISTER_LINK
            ))
            logger.info(f"🎯 Live signal sent at {signal_time_str} | Target: {target}x")
            
            # Wait 5 minutes for success message
            await asyncio.sleep(300)
            
            # === 3. SEND SUCCESS MESSAGE ===
            next_signal_time_str = next_signal_dt.strftime("%I:%M %p").lstrip("0")
            await broadcast(SUCCESS_MSG.format(
                target=target,
                signal_time=signal_time_str,
                profit_100=f"{profit_100:,}",
                profit_50=f"{profit_50:,}",
                link=REGISTER_LINK
            ))
            logger.info(f"✅ Success sent for {signal_time_str} | Next signal at {next_signal_time_str}")
        
        # Sleep to check again
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
    logger.info(f"📤 Sent to all {len(GROUP_CHAT_IDS)} groups")

# ========================= HEALTH =========================
@app.route('/health')
def health():
    now = datetime.now(ist)
    signal_dt, alert_dt, next_signal_dt = get_next_signal_time(now)
    
    return jsonify({
        "status": "LIVE - 15 MIN SIGNAL BOT",
        "current_time": now.strftime("%I:%M:%S %p").lstrip("0"),
        "next_alert": alert_dt.strftime("%I:%M %p").lstrip("0"),
        "next_signal": signal_dt.strftime("%I:%M %p").lstrip("0"),
        "next_success": (signal_dt + timedelta(minutes=5)).strftime("%I:%M %p").lstrip("0"),
        "time_until_alert": int((alert_dt - now).total_seconds()),
        "promocode": PROMOCODE,
        "schedule": "Every 15 mins: Alert at -5min, Live at 00/15/30/45, Success at +5min"
    })

# ========================= START =========================
def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(signal_scheduler())

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    logger.info("=" * 60)
    logger.info("🚀 LUCKY JET 15-MIN SIGNAL BOT STARTED")
    logger.info("📅 Schedule: Every 15 minutes")
    logger.info("⏰ Flow: Alert 5 min before → Live at exact time → Success 5 min after")
    logger.info("=" * 60)
    app.run(host='0.0.0.0', port=PORT, use_reloader=False)
