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
TIMEZONE = os.getenv('TIMEZONE', 'UTC')
CURRENCY_SYMBOL = "$"
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

# ========================= THRESHOLDS =========================
MIN_ONLINE_PER_GROUP = 390
MIN_DEPOSITS_LAST_10M = 72
MIN_HOT_GROUPS_REQUIRED = len(GROUP_CHAT_IDS) // 2 + 1
CHECK_INTERVAL = 50
SIGNAL_COOLDOWN = timedelta(minutes=44)

# ========================= KEYBOARD (FIXED!) =========================
def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("DEPOSIT $100 → GET $600 (500% BONUS)", url=REGISTER_LINK)],
        [InlineKeyboardButton("ACTIVATE BETWIN190 BONUS NOW", url=REGISTER_LINK)],
        [InlineKeyboardButton("REGISTER & PLAY — INSTANT WITHDRAWAL", url=REGISTER_LINK)]
    ])

# ========================= MESSAGES (MAX CONVERSION) =========================
PRE_SIGNAL = """VOLATILITY 100 INDEX JUST TRIGGERED
Lucky Jet is in **GOD MODE** right now — ALL regions exploding!

Players Online: **{online}+**
Deposits (last 9 min): **{deposits}+** and climbing fast
Next cashout predicted: **~{preview}x** in <5 minutes

Only 39 VIP seats remain before auto-cashout locks
This is the one you've been waiting for

[GET +500% BONUS → BETWIN190]({link})"""

LIVE_SIGNAL = """LIVE SIGNAL — ENTER RIGHT NOW

Game: **Lucky Jet**
Time: **{time}** (UTC)
Cash Out At: **{multiplier}×**  ← LOCKED IN
Accuracy: **99.4%** (last 12 hits: 11 wins)
Last 5: 7.8x · 9.1x · 12.6x · 18.3x → **24.7x**

$100 becomes **${profit}** in seconds
$50 → ${half_profit}

You have 23 seconds. Legends don’t hesitate.

[INSTANT DEPOSIT → BETWIN190 ACTIVE]({link})"""

SUCCESS = """SIGNAL SMASHED: **+{multiplier}x** JUST HIT

Total group profit this round: **{currency}{total:,}+** confirmed
Top reported: $100 → ${win}
Average per winner: **${avg}+**

97 members just cashed out big

Type “PAID” if you ate tonight

Next 15x–30x monster loading in ~40 mins…
Stay ready."""

GUIDE = """HOW TO COLLECT EVERY SIGNAL (25 sec setup)

1. Tap button → {link}
2. Register in 20 seconds
3. Enter promo: **BETWIN190**
4. Deposit $100 → Receive **$600** instantly
5. Open Lucky Jet → Auto-follow signals → Profit

+500% bonus valid today only
Instant withdrawal · 100% trusted

[CLAIM BONUS BEFORE NEXT SIGNAL → BETWIN190]({link})

Next explosion in ~40 min. Don’t sleep on this."""

# ========================= ACTIVITY SIMULATOR =========================
async def get_group_heat():
    hot_count = 0
    total_online = 0
    total_deposits = 0  # ← fixed

    for chat_id in GROUP_CHAT_IDS:
        try:
            chat = await bot.get_chat(chat_id)
            member_count = chat.get_members_count() or 1350

            hour = datetime.now(ZoneInfo(TIMEZONE)).hour
            base_ratio = 0.31 if 12 <= hour <= 23 else 0.19
            online = int(member_count * base_ratio * random.uniform(0.9, 1.35)) + random.randint(40, 160)
            deposits = random.randint(58, 142) if online > 360 else random.randint(22, 68)

            total_online += online
            total_deposits += deposits

            if online >= MIN_ONLINE_PER_GROUP and deposits >= MIN_DEPOSITS_LAST_10M:
                hot_count += 1
        except Exception as e:
            logger.warning(f"Chat {chat_id} error: {e}")
            continue

    avg_online = total_online // len(GROUP_CHAT_IDS) if GROUP_CHAT_IDS else 0

    return {
        "hot_groups": hot_count,
        "avg_online": avg_online,
        "total_deposits": total_deposits,
        "is_peak": hot_count >= MIN_HOT_GROUPS_REQUIRED and avg_online >= 410
    }

# ========================= BROADCAST =========================
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
            await asyncio.sleep(0.75)
        except TelegramError as e:
            logger.error(f"Send failed {chat_id}: {e}")
    logger.info(f"Sent to {sent}/{len(GROUP_CHAT_IDS)} groups")

# ========================= MAIN ENGINE =========================
last_signal_time = None

async def peak_signal_engine():
    global last_signal_time
    logger.info("BETWIN190 PEAK-ONLY BOT STARTED — Fires only on real heat")

    while True:
        try:
            now = datetime.now(ZoneInfo(TIMEZONE))
            heat = await get_group_heat()

            if last_signal_time and (now - last_signal_time) < SIGNAL_COOLDOWN:
                await asyncio.sleep(CHECK_INTERVAL)
                continue

            if heat["is_peak"] and heat["avg_online"] >= 410:
                logger.info(f"PEAK → {heat['avg_online']} online | {heat['total_deposits']} deposits")

                # Pre-signal
                preview_x = round(random.uniform(12.5, 27.0), 1)
                await broadcast(PRE_SIGNAL.format(
                    online=f"{heat['avg_online']:,}",
                    deposits=heat['total_deposits'],
                    preview=preview_x,
                    link=REGISTER_LINK
                ))
                await asyncio.sleep(300)

                # Live signal
                multiplier = round(random.uniform(10.8, 28.0), 2)
                profit = int(100 * multiplier)
                half_profit = int(50 * multiplier)

                await broadcast(LIVE_SIGNAL.format(
                    time=now.strftime("%H:%M"),
                    multiplier=multiplier,
                    profit=f"{profit:,}",
                    half_profit=f"{half_profit:,}",
                    link=REGISTER_LINK
                ))

                last_signal_time = now

                # Success + Guide
                await asyncio.sleep(180)
                total_profit = random.randint(13800, 32600)
                await broadcast(SUCCESS.format(
                    multiplier=multiplier,
                    total=total_profit,
                    currency=CURRENCY_SYMBOL,
                    win=f"{profit:,}",
                    avg=random.randint(520, 1100)
                ))
                await asyncio.sleep(10)
                await broadcast(GUIDE.format(link=REGISTER_LINK))

                logger.info(f"Cycle done → {multiplier}x | Next in ~44 min")

            await asyncio.sleep(CHECK_INTERVAL)

        except Exception as e:
            logger.error(f"Engine error: {e}")
            await asyncio.sleep(60)

# ========================= HEALTH =========================
@app.route('/health')
def health():
    return jsonify({
        "status": "LIVE - PEAK MODE",
        "promocode": PROMOCODE,
        "daily_signals": "4–8",
        "last_check": datetime.now(ZoneInfo(TIMEZONE)).isoformat()
    })

# ========================= START =========================
def run_bot():
    asyncio.run(peak_signal_engine())

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    logger.info("LUCKY JET BETWIN190 BOT IS NOW LIVE & ONLY SENDS DURING PEAKS")
    app.run(host='0.0.0.0', port=PORT, use_reloader=False)
