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

# Daily operation hours (22:00 to 01:00 IST)
ACTIVE_HOURS_START = 22  # 10 PM
ACTIVE_HOURS_END = 1     # 1 AM (next day)

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

if not BOT_TOKEN or not GROUP_CHAT_IDS:
    logger.error("BOT_TOKEN or GROUP_CHAT_IDS missing!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)
ist = ZoneInfo(TIMEZONE_IST)

# ========================= KEYBOARDS =========================
def get_alert_keyboard():
    """Keyboard for alert message"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📲 Register Now", url=REGISTER_LINK)],
        [InlineKeyboardButton("🎮 Enter Aviator", url=REGISTER_LINK)]
    ])

def get_live_keyboard():
    """Keyboard for live signal"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ INSTANT DEPOSIT", url=REGISTER_LINK)],
        [InlineKeyboardButton("🚀 PLAY NOW", url=REGISTER_LINK)]
    ])

def get_success_keyboard():
    """Keyboard for success message"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 DEPOSIT FOR NEXT", url=REGISTER_LINK)],
        [InlineKeyboardButton("📊 CHECK STATS", url=REGISTER_LINK)]
    ])

# ========================= MESSAGES (Aviator Edition) =========================

# Alert: 5 mins before signal
ALERT_MSG = """🚨 **UPCOMING SIGNAL IN 5 MINUTES**

⏰ **Time**: {signal_time} IST
🎯 **Expected**: ~{preview}x

✅ High accuracy Aviator signal loading!
🤑 Members are already positioning...

**Code:** `{promocode}`"""

# Live Signal: Exact time
LIVE_MSG = """🔥 **LIVE SIGNAL — ENTER NOW**

🎮 **Game**: AVIATOR
⏰ **Time**: {signal_time} IST
🎯 **Target**: **{target}x** (Cashout)

💸 **Potential Returns:**
• $100 → ${profit_100}
• $50 → ${profit_50}

⏳ Enter in next 20 seconds!

📈 Last 10 signals: 9 Wins ✅

**Use Code:** `{promocode}`"""

# Success: 5 mins after live signal
SUCCESS_MSG = """✅ **SIGNAL HIT SUCCESSFULLY!**

🎯 **{target}x HIT** at {signal_time} IST

💰 Members who followed → PAID OUT!

📊 **Example Returns:**
• $100 → ${profit_100} 
• $50 → ${profit_50}

👇 Drop **"PAID"** if you won!

🔄 Next signal in 10 minutes...

**Code for Bonus:** `{promocode}`"""

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
        signal_dt = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        signal_dt = now.replace(minute=next_15, second=0, microsecond=0)
    
    # Alert is 5 minutes before next signal
    alert_dt = signal_dt - timedelta(minutes=5)
    
    # Calculate the signal after next
    next_next_15 = next_15 + 15
    if next_next_15 >= 60:
        next_signal_dt = signal_dt.replace(minute=0) + timedelta(hours=1)
    else:
        next_signal_dt = signal_dt.replace(minute=next_next_15)
    
    return signal_dt, alert_dt, next_signal_dt

def is_active_hours(now: datetime) -> bool:
    """Check if current time is within active hours (10 PM to 1 AM)"""
    current_hour = now.hour
    
    # Handle overnight period (10 PM to 1 AM next day)
    if current_hour >= ACTIVE_HOURS_START or current_hour < ACTIVE_HOURS_END:
        return True
    return False

# ========================= MAIN SCHEDULER =========================
async def signal_scheduler():
    while True:
        now = datetime.now(ist)
        current_time_str = now.strftime("%I:%M:%S %p").lstrip("0")
        
        # Check if within active hours
        if not is_active_hours(now):
            logger.info(f"⏸️ Outside active hours ({current_time_str}). Sleeping 60s...")
            await asyncio.sleep(60)
            continue
            
        # Calculate next signal times
        signal_dt, alert_dt, next_signal_dt = get_next_signal_time(now)
        signal_time_str = signal_dt.strftime("%I:%M %p").lstrip("0")
        alert_time_str = alert_dt.strftime("%I:%M %p").lstrip("0")
        
        # Check if it's time to send alert (5 mins before next signal)
        time_to_alert = (alert_dt - now).total_seconds()
        
        if 0 <= time_to_alert < 60:  # Within next minute
            logger.info(f"🔔 ALERT DETECTED → Current: {current_time_str}, Alert: {alert_time_str}, Signal: {signal_time_str}")
            
            # Generate signal data
            target = round(random.uniform(2.5, 8.0), 1)  # Aviator typically lower multipliers
            preview = round(target + random.uniform(-0.5, 1.5), 1)
            
            # === 1. SEND ALERT ===
            await broadcast(
                message=ALERT_MSG.format(
                    signal_time=signal_time_str,
                    preview=preview,
                    promocode=PROMOCODE
                ),
                keyboard=get_alert_keyboard()
            )
            logger.info(f"✅ Alert sent for {signal_time_str} (Target: {target}x)")
            
            # Wait until exact signal time
            wait_seconds = (signal_dt - now).total_seconds()
            if wait_seconds > 0:
                logger.info(f"⏳ Waiting {int(wait_seconds)}s for live signal at {signal_time_str}")
                await asyncio.sleep(wait_seconds)
            
            # === 2. SEND LIVE SIGNAL ===
            profit_100 = int(100 * (target - 1))
            profit_50 = int(50 * (target - 1))
            
            await broadcast(
                message=LIVE_MSG.format(
                    signal_time=signal_time_str,
                    target=target,
                    profit_100=f"{profit_100:,}",
                    profit_50=f"{profit_50:,}",
                    promocode=PROMOCODE
                ),
                keyboard=get_live_keyboard()
            )
            logger.info(f"🎯 Live signal sent at {signal_time_str} | Target: {target}x")
            
            # Wait 5 minutes for success message
            await asyncio.sleep(300)
            
            # === 3. SEND SUCCESS MESSAGE ===
            next_signal_time_str = next_signal_dt.strftime("%I:%M %p").lstrip("0")
            await broadcast(
                message=SUCCESS_MSG.format(
                    target=target,
                    signal_time=signal_time_str,
                    profit_100=f"{profit_100:,}",
                    profit_50=f"{profit_50:,}",
                    promocode=PROMOCODE
                ),
                keyboard=get_success_keyboard()
            )
            logger.info(f"✅ Success sent for {signal_time_str} | Next: {next_signal_time_str}")
        
        # Sleep to check again
        await asyncio.sleep(10)

# ========================= BROADCAST =========================
async def broadcast(message: str, keyboard: InlineKeyboardMarkup):
    for chat_id in GROUP_CHAT_IDS:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown",
                disable_web_page_preview=True,
                reply_markup=keyboard
            )
            await asyncio.sleep(0.8)
        except TelegramError as e:
            logger.error(f"❌ Send failed {chat_id}: {e}")
    logger.info(f"📤 Sent to {len(GROUP_CHAT_IDS)} group(s)")

# ========================= HEALTH =========================
@app.route('/health')
def health():
    now = datetime.now(ist)
    signal_dt, alert_dt, next_signal_dt = get_next_signal_time(now)
    
    active_status = "ACTIVE" if is_active_hours(now) else "INACTIVE (10 PM-1 AM only)"
    
    return jsonify({
        "status": f"LIVE - AVIATOR SIGNAL BOT [{active_status}]",
        "current_time": now.strftime("%I:%M:%S %p").lstrip("0"),
        "active_hours": f"{ACTIVE_HOURS_START}:00 - {ACTIVE_HOURS_END}:00 IST",
        "is_active_now": is_active_hours(now),
        "next_alert": alert_dt.strftime("%I:%M %p").lstrip("0"),
        "next_signal": signal_dt.strftime("%I:%M %p").lstrip("0"),
        "time_until_alert": int((alert_dt - now).total_seconds()),
        "promocode": PROMOCODE,
        "game": "Aviator",
        "schedule": "Every 15 mins: Alert(-5m) → Live → Success(+5m)",
        "groups": len(GROUP_CHAT_IDS)
    })

@app.route('/')
def home():
    return "<h3>🚀 Aviator Signal Bot is Running</h3><p>Check /health for status</p>"

# ========================= START =========================
def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(signal_scheduler())

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    logger.info("=" * 60)
    logger.info("🚀 AVIATOR SIGNAL BOT STARTED")
    logger.info(f"🎮 Game: Aviator")
    logger.info(f"⏰ Active Hours: {ACTIVE_HOURS_START}:00 to {ACTIVE_HOURS_END}:00 IST")
    logger.info(f"📅 Schedule: Every 15 minutes during active hours")
    logger.info(f"📊 Flow: Alert 5m before → Live → Success 5m after")
    logger.info(f"👥 Groups: {len(GROUP_CHAT_IDS)}")
    logger.info("=" * 60)
    app.run(host='0.0.0.0', port=PORT, use_reloader=False)
