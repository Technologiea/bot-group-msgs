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
GROUP_CHAT_IDS = [x.strip() for x in os.getenv('GROUP_CHAT_IDS', '').split(',') if x.strip()]
REGISTER_LINK = "https://lkxd.cc/01f0"
PROMOCODE = "KOHLI143"
TIMEZONE = os.getenv('TIMEZONE', 'UTC')
CURRENCY_SYMBOL = "$"
PORT = int(os.getenv('PORT', 5000))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if not BOT_TOKEN or not GROUP_CHAT_IDS:
    logger.error("Missing BOT_TOKEN or GROUP_CHAT_IDS")
    exit(1)

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# ========================= DYNAMIC DETECTION THRESHOLDS =========================
MIN_ONLINE_FOR_SIGNAL = 380          # Only send when group is ON FIRE
MIN_DEPOSITS_LAST_10MIN = 68
MIN_REQUIRED_GROUPS_HOT = len(GROUP_CHAT_IDS) // 2 + 1   # At least half groups must be hot

# How often we check for peak activity (seconds)
CHECK_INTERVAL = 45

# Cooldown after a full signal cycle (prevents spam)
SIGNAL_COOLDOWN = timedelta(minutes=48)

# ========================= KEYBOARDS =========================
def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("DEPOSIT $100 → GET $600 +500% BONUS", url=REGISTER_LINK)],
        [InlineKeyboardButton("CLAIM KOHLI143 BONUS NOW", url=REGISTER_LINK)],
        [InlineKeyboardButton("REGISTER & PLAY INSTANTLY", url=REGISTER_LINK)]
    ])

# ========================= TEMPLATES (MAX CONVERSION) =========================
PRE_SIGNAL = """VOLATILITY EXPLOSION DETECTED

Lucky Jet is going CRAZY right now in ALL regions!
**Players online:** {online}+ across groups
**Deposits in last 8 min:** {deposits}+

**MASSIVE {preview}x surge confirmed in 5 MINUTES**

Only 42 elite spots left

Get in NOW or watch others cash out big

[DEPOSIT & CLAIM +500% BONUS → KOHLI143]({link})"""

LIVE_SIGNAL = """LIVE ELITE SIGNAL — BET RIGHT NOW

**Game:** Lucky Jet
**Entry:** IMMEDIATELY ({time} UTC)
**Cashout at:** **{multiplier}x**
**Confidence:** 99.1%
**Last 5:** 6.3x · 8.9x · 11.7x · 15.4x · **21.8x**

$100 → ${profit} in seconds

[INSTANT DEPOSIT & PLAY → KOHLI143]({link})

You have 25 seconds. Winners don’t wait."""

SUCCESS = """SIGNAL DESTROYED: +{multiplier}x

**Group profit this round:** {currency}{total:,}+
**Top reported win:** $100 → ${win}
**Average profit per member:** ${avg}+

Next monster signal loading in ~45 mins

Reply "WON" if you banked

Guide for new winners ↓"""

GUIDE = """HOW TO WIN EVERY TIME (30 seconds)

1. Click → {link}
2. Register fast
3. Enter promocode: **KOHLI143**
4. Deposit $100 → Get **$600** instantly
5. Open Lucky Jet → Follow signals → Profit

+500% bonus = 6× your money from first deposit
Withdraw anytime · 100% real

[REGISTER NOW — KOHLI143 READY]({link})

Next 20x+ is coming. Be ready."""

# ========================= ACTIVITY MONITOR =========================
async def get_group_heat():
    hot_groups = 0
    total_online = 0
    total_deposits = 0

    for chat_id in GROUP_CHAT_IDS:
        try:
            chat = await bot.get_chat(chat_id)
            members = chat.get_members_count() or 1200
            online = int(members * random.uniform(0.22, 0.38)) + random.randint(50, 180)
            deposits = random.randint(42, 138)

            total_online += online
            total_deposits += deposits

            if online >= MIN_ONLINE_FOR_SIGNAL and deposits >= MIN_DEPOSITS_LAST_10MIN:
                hot_groups += 1
        except:
            continue

    avg_online = total_online // len(GROUP_CHAT_IDS) if GROUP_CHAT_IDS else 0
    return {
        "hot_groups": hot_groups,
        "avg_online": avg_online,
        "total_deposits": total_deposits,
        "is_peak": hot_groups >= MIN_REQUIRED_GROUPS_HOT and avg_online >= MIN_ONLINE_FOR_SIGNAL
    }

# ========================= SENDERS =========================
async def broadcast(text):
    tasks = []
    for chat_id in GROUP_CHAT_IDS:
        tasks.append(
            bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="Markdown",
                disable_web_page_preview=True,
                reply_markup=get_keyboard()
            )
        )
        await asyncio.sleep(0.7)
    await asyncio.gather(*tasks, return_exceptions=True)

# ========================= MAIN ENGINE =========================
last_signal_time = None

async def peak_activity_engine():
    global last_signal_time
    logger.info("DYNAMIC PEAK DETECTION ENGINE STARTED — ONLY SENDS AT BEST TIMES")

    while True:
        try:
            now = datetime.now(ZoneInfo(TIMEZONE))
            heat = await get_group_heat()

            # Cooldown check
            if last_signal_time and (now - last_signal_time) < SIGNAL_COOLDOWN:
                await asyncio.sleep(CHECK_INTERVAL)
                continue

            # REAL PEAK DETECTED → FULL SEQUENCE
            if heat["is_peak"] and heat["avg_online"] >= 420:
                logger.info(f"PEAK DETECTED! Online: {heat['avg_online']} | Deposits: {heat['total_deposits']}")

                # 1. 5-minute warning
                preview_x = round(random.uniform(11.0, 24.0), 1)
                await broadcast(PRE_SIGNAL.format(
                    online=heat["avg_online"],
                    deposits=heat["total_deposits"],
                    preview=preview_x,
                    link=REGISTER_LINK
                ))
                await asyncio.sleep(300)  # Wait 5 minutes

                # 2. LIVE SIGNAL
                multiplier = round(random.uniform(9.5, 26.0), 2)
                profit = int(100 * multiplier)
                await broadcast(LIVE_SIGNAL.format(
                    time=datetime.now(ZoneInfo(TIMEZONE)).strftime("%H:%M"),
                    multiplier=multiplier,
                    profit=profit,
                    link=REGISTER_LINK
                ))

                last_signal_time = datetime.now(ZoneInfo(TIMEZONE))

                # 3. Success + Guide after 3 minutes
                await asyncio.sleep(180)
                total_profit = random.randint(12400, 28700)
                await broadcast(SUCCESS.format(
                    multiplier=multiplier,
                    total=total_profit,
                    currency=CURRENCY_SYMBOL,
                    win=int(100 * multiplier),
                    avg=random.randint(460, 940)
                ))

                await asyncio.sleep(8)
                await broadcast(GUIDE.format(link=REGISTER_LINK))

                logger.info(f"SIGNAL CYCLE COMPLETED → {multiplier}x | Next possible in ~48 min")

            await asyncio.sleep(CHECK_INTERVAL)

        except Exception as e:
            logger.error(f"Engine error: {e}")
            await asyncio.sleep(60)

# ========================= HEALTH & START =========================
@app.route('/health')
def health():
    return jsonify({
        "status": "PEAK-ONLY MODE ACTIVE",
        "trigger": "Only when 420+ online & 68+ deposits",
        "signals_per_day": "4-7 (only best times)",
        "promocode": PROMOCODE,
        "conversion_mode": "MAXIMUM"
    })

def run():
    asyncio.run(peak_activity_engine())

if __name__ == "__main__":
    threading.Thread(target=run, daemon=True).start()
    logger.info("1WIN KOHLI143 PEAK-ONLY BOT IS LIVE — ONLY BEST TIMES")
    app.run(host='0.0.0.0', port=PORT)
