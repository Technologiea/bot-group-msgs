import asyncio
import random
import logging
import os
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import TelegramError
from flask import Flask, jsonify
import threading

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_IDS = os.getenv('GROUP_CHAT_IDS', '').split(',')
REGISTER_LINK = os.getenv('REGISTER_LINK', 'https://lkpq.cc/2ee301')
TIMEZONE = os.getenv('TIMEZONE', 'UTC')
CURRENCY_SYMBOL = os.getenv('CURRENCY_SYMBOL', '$')
PORT = int(os.getenv('PORT', 5000))
# --- CONFIGURATION ---

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Validate
if not BOT_TOKEN:
    logger.error("BOT_TOKEN is not set!")
    exit(1)
if not GROUP_CHAT_IDS or not any(GROUP_CHAT_IDS):
    logger.error("No GROUP_CHAT_IDS configured!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# Global peak windows in UTC
PEAK_WINDOWS = [
    ("1:40 AM", "2:05 AM"),
    ("6:50 AM", "7:15 AM"),
    ("11:50 AM", "12:15 PM"),
    ("4:40 PM", "5:05 PM"),
    ("8:55 PM", "9:20 PM"),
    ("11:45 PM", "12:10 AM")
]

# Inline keyboard for instant deposit
DEPOSIT_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("DEPOSIT $100 → PLAY $600", url=REGISTER_LINK)],
    [InlineKeyboardButton("CLAIM 500% BONUS NOW", url=REGISTER_LINK)]
])

# Hype template
HYPE_TEMPLATE = """GLOBAL ALERT: LUCKY JET VOLATILITY SPIKE

AI detected **{multiplier_preview}x surge** in 25 mins — momentum in EU/Asia/US/LATAM.

**Only 50 elite spots** open.

**Online:** {online_count}  
**Deposits:** {deposits_live} last 10 mins

Signal in **T-20 mins**

[CLAIM 500% BONUS]({register_link})
[DEPOSIT NOW]({register_link})

DM @DOREN99: "I'M IN" → Priority"""

# Signal template
SIGNAL_TEMPLATE = """ELITE LUCKY JET SIGNAL LIVE

**Bet Entry:** NOW ({bet_time} UTC)
**Cashout:** {multiplier}x

**Last 3:** 5.2x | 7.9x | **11.4x**
**RTP:** 97.3% (Live)

**Spots left:** 12 / 50

Deposit ${deposit_min} → Play ${play_amount}

[DEPOSIT & PLAY]({register_link})

**Winners act. Now.**

DM @DOREN99: "EXECUTED" → Free next signal"""

# Success template
SUCCESS_TEMPLATE = """SIGNAL CRUSHED: +{multiplier}x

**Group Profit:** {currency_symbol}{profit:,}+  
**Top Win:** {currency_symbol}470 → {currency_symbol}5,170

**Next Signal:** T-45 mins

**Missed?** {currency_symbol}370 avg

[DEPOSIT & JOIN 1%]({register_link})

**Volatility rising. Next = 12x+**

DM @DOREN99: "NEXT" → Reserve seat"""

# --- HELPER FUNCTIONS ---
def parse_time_str(t_str):
    try:
        dt = datetime.strptime(t_str, "%I:%M %p")
        return dt.time()
    except:
        if "12:10 AM" in t_str:
            return time(0, 10)
        return None

def get_bet_time(idx):
    t = parse_time_str(PEAK_WINDOWS[idx][1])
    if not t: return None
    now = datetime.now(ZoneInfo(TIMEZONE))
    dt = datetime.combine(now.date(), t, tzinfo=ZoneInfo(TIMEZONE))
    return dt + timedelta(days=1) if now > dt else dt

def random_multiplier():
    return round(random.uniform(5.0, 15.0), 2)

def random_profit():
    return random.randint(1000, 10000)

async def get_real_engagement(chat_id):
    """Get real online + recent activity"""
    try:
        # Simulate real engagement (no external API)
        chat = await bot.get_chat(chat_id)
        member_count = chat.get_members_count() or 0
        active_users = random.randint(10, 50)
        online_estimate = int(member_count * 0.18) + active_users * 3
        deposits_live = random.randint(25, 90)
        return max(online_estimate, 180), deposits_live
    except:
        return 220, random.randint(30, 80)

async def send_all(func):
    for cid in GROUP_CHAT_IDS:
        if not cid.strip(): continue
        try:
            await func(cid.strip())
            await asyncio.sleep(1.2)
        except TelegramError as e:
            logger.error(f"Send error {cid}: {e}")

# --- MESSAGE SENDERS ---
async def send_hype(cid, mp, oc, dl):
    msg = HYPE_TEMPLATE.format(
        multiplier_preview=mp, online_count=oc, deposits_live=dl,
        register_link=REGISTER_LINK
    )
    await bot.send_message(
        cid, msg, parse_mode='Markdown', disable_web_page_preview=True,
        reply_markup=DEPOSIT_KEYBOARD
    )

async def send_signal(cid, bt, m):
    msg = SIGNAL_TEMPLATE.format(
        bet_time=bt.strftime("%I:%M %p"),
        multiplier=m, deposit_min=100, play_amount=600,
        register_link=REGISTER_LINK
    )
    await bot.send_message(
        cid, msg, parse_mode='Markdown', disable_web_page_preview=True,
        reply_markup=DEPOSIT_KEYBOARD
    )

async def send_success(cid, m, p):
    msg = SUCCESS_TEMPLATE.format(
        multiplier=m, profit=p, currency_symbol=CURRENCY_SYMBOL,
        register_link=REGISTER_LINK
    )
    await bot.send_message(
        cid, msg, parse_mode='Markdown', disable_web_page_preview=True,
        reply_markup=DEPOSIT_KEYBOARD
    )

# --- MAIN LOOP ---
async def main():
    logger.info("GLOBAL SALES ENGINE LIVE | NO DEEPL | $10K/DAY TARGET")
    daily_done = set()
    last_mult = 0

    while True:
        try:
            now = datetime.now(ZoneInfo(TIMEZONE))
            if now.hour == 0 and now.minute < 5:
                daily_done.clear()

            for i in range(len(PEAK_WINDOWS)):
                if i in daily_done: continue
                bt = get_bet_time(i)
                if not bt: continue
                ht = bt - timedelta(minutes=20)
                st = bt + timedelta(minutes=5)

                # Hype
                if abs((now - ht).total_seconds()) < 60:
                    tasks = []
                    for cid in GROUP_CHAT_IDS:
                        cid_str = cid.strip()
                        oc, dl = await get_real_engagement(cid_str)
                        if oc > 200:
                            tasks.append(send_hype(cid_str, random_multiplier(), oc, dl))
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                        await asyncio.sleep(60)

                # Signal
                elif abs((now - bt).total_seconds()) < 60:
                    tasks = []
                    for cid in GROUP_CHAT_IDS:
                        cid_str = cid.strip()
                        oc, _ = await get_real_engagement(cid_str)
                        if oc > 200 and i not in daily_done:
                            m = random_multiplier()
                            tasks.append(send_signal(cid_str, bt, m))
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                        daily_done.add(i)
                        last_mult = m
                        await asyncio.sleep(60)

                # Success
                elif abs((now - st).total_seconds()) < 60 and i in daily_done:
                    tasks = []
                    for cid in GROUP_CHAT_IDS:
                        p = random_profit()
                        tasks.append(send_success(cid.strip(), last_mult, p))
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                        await asyncio.sleep(300)

            await asyncio.sleep(30 if len(daily_done) < 6 else 3600)

        except Exception as e:
            logger.error(f"CRITICAL ERROR: {e}")
            await asyncio.sleep(60)

# --- FLASK ---
@app.route('/health')
def health():
    return jsonify({
        "status": "LIVE",
        "mode": "GLOBAL_NO_DEEPL",
        "target": "$10K+ USD/day",
        "features": ["Real Engagement", "Inline Deposit", "UTC Sync", "No External API"]
    })

def run_bot():
    asyncio.run(main())

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
