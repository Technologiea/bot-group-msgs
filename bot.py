import asyncio
import random
import logging
import os
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from telegram import Bot
from telegram.error import TelegramError
from flask import Flask, jsonify
import threading

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_IDS = os.getenv('GROUP_CHAT_IDS', '').split(',')
REGISTER_LINK = os.getenv('REGISTER_LINK', 'https://lkpq.cc/eec3')
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Kolkata')
CURRENCY_SYMBOL = os.getenv('CURRENCY_SYMBOL', '₹')
PORT = int(os.getenv('PORT', 5000))
# --- CONFIGURATION ---

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Validate environment variables
if not BOT_TOKEN:
    logger.error("BOT_TOKEN is not set!")
    exit(1)
if not GROUP_CHAT_IDS or not any(GROUP_CHAT_IDS):
    logger.error("No GROUP_CHAT_IDS configured!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# Dynamic high-engagement windows: (hype_time_str, bet_time_str) in 12h format for display
PEAK_WINDOWS = [
    ("10:35 AM", "11:00 AM"),  # Morning rush
    ("1:40 PM", "2:05 PM"),    # Lunch break surge (adjusted for +20min)
    ("2:50 PM", "3:15 PM"),    # Post-lunch dopamine
    ("6:40 PM", "7:05 PM"),    # Evening unwind
    ("8:55 PM", "9:20 PM"),    # Prime time hype
    ("11:45 PM", "12:10 AM")   # Midnight gamblers
]

# Pre-signal hype template
HYPE_TEMPLATE = """LIVE ALERT: LUCKY JET VOLATILITY SPIKE DETECTED

🔥 Our AI just flagged a **{multiplier_preview}x potential ascent** in the next 25 mins.

💎 **Only 50 elite spots open** for this 1win Lucky Jet signal.

👥 **Current online:** {online_count} warriors  
⚡ **Deposits live:** {deposits_live} in last 10 mins

⏰ Signal drops in **T-20 mins** – Prepare to execute.

🔗 [SECURE 500% BONUS NOW]({register_link})
👉 [DEPOSIT & LOCK YOUR SPOT]({register_link})

💬 DM @DOREN99 — "I'M IN" for priority access."""

# Elite signal template
SIGNAL_TEMPLATE = """🚀 *ELITE LUCKY JET SIGNAL DEPLOYED* 🚀

⏰ **Bet Entry:** NOW ({bet_time})
🎯 **Cashout Target:** {multiplier}x

📊 **Live Proof:** Last 3 signals → 5.2x | 7.9x | **11.4x**
💹 **1win RTP Edge:** 97.3% this hour (verified analytics)

🛡️ **Spots left:** 12 / 50 – High engagement window active.

🔥 Transform {currency_symbol}500 into {currency_symbol}3,000+ with 500% bonus.

🔗 [DEPOSIT ₹500 → PLAY ₹3,000]({register_link})

**Winners execute. Losers hesitate.**

💬 DM @DOREN99: "EXECUTED" → Unlock next signal **FREE**."""

# Success blast template
SUCCESS_TEMPLATE = """✅ *SIGNAL EXECUTED: +{multiplier}x LOCKED* ✅

💰 **Group Profit:** {currency_symbol}{profit:,}+  
🏅 **Top Winner:** {currency_symbol}47,000 → {currency_symbol}517,000

🔥 **Trend Confirmed:** Volatility climbing – Next play = **12x+ potential**

⏰ **Next signal:** T-45 mins. **Spots filling fast.** (Peak engagement ahead)

⚠️ **Non-depositors missed:** ₹37,000 avg profit.

🔗 [DEPOSIT NOW & JOIN THE 1% WINNERS]({register_link})

💡 **Pro Move:** Scale deposits, lock wins – 1win's seamless payouts await.

💬 DM @DOREN99: "NEXT" → Reserve your elite seat."""

def parse_time_str(time_str):
    """Parse 12h time str to datetime.time"""
    try:
        return datetime.strptime(time_str, "%I:%M %p").time()
    except:
        return None

def get_bet_time_from_window(window_idx):
    """Get bet time for today or tomorrow based on window"""
    bet_str = PEAK_WINDOWS[window_idx][1]
    bet_time_obj = parse_time_str(bet_str)
    now = datetime.now(ZoneInfo(TIMEZONE))
    bet_today = datetime.combine(now.date(), bet_time_obj, tzinfo=ZoneInfo(TIMEZONE))
    if now > bet_today:
        bet_today += timedelta(days=1)
    return bet_today

def random_high_multiplier():
    return round(random.uniform(5.0, 15.0), 2)

def random_profit():
    return random.randint(50000, 200000) // 1000 * 1000  # Aspirational ₹50k-₹200k

def approximate_online_count():
    """Fallback approximation for high engagement (simulate >150)"""
    return random.randint(100, 300)  # Assume high during peaks

async def get_engagement_estimate():
    """Estimate total online/deposits across groups"""
    total_members = 0
    for chat_id in GROUP_CHAT_IDS:
        try:
            chat = await bot.get_chat(chat_id.strip())
            total_members += chat.get_members_count() or 0
        except:
            pass
    # Simulate online as fraction + random for dynamism
    online_estimate = int(total_members * 0.1 + random.randint(50, 200))
    deposits_live = random.randint(20, 60)
    return max(online_estimate, 150), deposits_live  # Threshold enforced

async def should_deploy_signal(window_idx):
    """Check if in peak window and engagement high"""
    now = datetime.now(ZoneInfo(TIMEZONE))
    hype_str, bet_str = PEAK_WINDOWS[window_idx]
    current_str = now.strftime("%I:%M %p").upper()
    if hype_str not in current_str and bet_str not in current_str:
        return False
    online, _ = await get_engagement_estimate()
    return online > 150  # Dynamic check

async def send_to_all_channels(message_func):
    for chat_id in GROUP_CHAT_IDS:
        if not chat_id.strip():
            continue
        try:
            await message_func(chat_id.strip())
            await asyncio.sleep(1)
        except TelegramError as e:
            logger.error(f"Error sending to {chat_id}: {e}")

async def send_hype_to_chat(chat_id, multiplier_preview, online_count, deposits_live):
    message = HYPE_TEMPLATE.format(
        multiplier_preview=multiplier_preview,
        online_count=online_count,
        deposits_live=deposits_live,
        register_link=REGISTER_LINK
    )
    await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown', disable_web_page_preview=True)
    logger.info(f"Hype sent to {chat_id}")

async def send_signal_to_chat(chat_id, bet_time, multiplier):
    message = SIGNAL_TEMPLATE.format(
        bet_time=bet_time.strftime("%I:%M %p"),
        multiplier=multiplier,
        currency_symbol=CURRENCY_SYMBOL,
        register_link=REGISTER_LINK
    )
    await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown', disable_web_page_preview=True)
    logger.info(f"Signal deployed to {chat_id} for {bet_time}")

async def send_success_to_chat(chat_id, multiplier, profit):
    message = SUCCESS_TEMPLATE.format(
        multiplier=multiplier,
        profit=profit,
        currency_symbol=CURRENCY_SYMBOL,
        register_link=REGISTER_LINK
    )
    await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown', disable_web_page_preview=True)
    logger.info(f"Success blast to {chat_id} with {multiplier}x")

async def main():
    logger.info("Dynamic Engine DEPLOYED: Hunting peak engagement for $2K+ daily.")
    print("Profit missile active. Targeting 6x signals/day in high-engagement windows.")
    
    daily_signals = set()  # Track deployed per day (window_idx)
    
    while True:
        try:
            now = datetime.now(ZoneInfo(TIMEZONE))
            today_str = now.date().isoformat()
            
            # Reset daily at midnight
            if now.hour == 0 and now.minute == 0:
                daily_signals.clear()
            
            deployed_today = len(daily_signals) >= len(PEAK_WINDOWS)
            
            for idx in range(len(PEAK_WINDOWS)):
                if idx in daily_signals:
                    continue
                
                bet_time = get_bet_time_from_window(idx)
                hype_time = bet_time - timedelta(minutes=20)
                success_time = bet_time + timedelta(minutes=5)
                
                # Hype deployment (20 min before bet)
                if abs((now - hype_time).total_seconds()) <= 60:
                    online, deposits = await get_engagement_estimate()
                    if online > 150:
                        multiplier_preview = random_high_multiplier()
                        logger.info(f"Deploying hype for window {idx}")
                        await send_to_all_channels(
                            lambda cid: send_hype_to_chat(cid, multiplier_preview, online, deposits)
                        )
                        await asyncio.sleep(60)
                    else:
                        logger.info(f"Low engagement, skipping hype for {idx}")
                
                # Signal deployment (at bet time)
                elif abs((now - bet_time).total_seconds()) <= 60:
                    online, _ = await get_engagement_estimate()
                    if online > 150 and idx not in daily_signals:
                        multiplier = random_high_multiplier()
                        logger.info(f"Deploying signal for window {idx}")
                        await send_to_all_channels(lambda cid: send_signal_to_chat(cid, bet_time, multiplier))
                        daily_signals.add(idx)
                        # Store for success (simple: use last multiplier)
                        last_multiplier = multiplier
                        await asyncio.sleep(60)
                    else:
                        logger.info(f"Engagement check failed or already sent for {idx}")
                
                # Success blast (5 min after)
                elif abs((now - success_time).total_seconds()) <= 60 and idx in daily_signals:
                    profit = random_profit()
                    logger.info(f"Blasting success for window {idx}")
                    await send_to_all_channels(lambda cid: send_success_to_chat(cid, last_multiplier, profit))
                    await asyncio.sleep(300)  # Cooldown after success
            
            if not deployed_today:
                await asyncio.sleep(30)  # Frequent checks during day
            else:
                # Sleep to next day first window
                next_day_first = datetime.combine(now.date() + timedelta(days=1), parse_time_str(PEAK_WINDOWS[0][1]), tzinfo=ZoneInfo(TIMEZONE))
                sleep_sec = (next_day_first - now).total_seconds()
                logger.info(f"All signals deployed. Sleeping {sleep_sec/3600:.1f} hrs to next cycle.")
                await asyncio.sleep(sleep_sec)
            
        except Exception as e:
            logger.error(f"Engine error: {e}")
            await asyncio.sleep(60)

@app.route('/health')
def health_check():
    return jsonify({"status": "dynamic", "target": "$2K+ daily conversions"})

def run_bot():
    asyncio.run(main())

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    app.run(host='0.0.0.0', port=PORT)
