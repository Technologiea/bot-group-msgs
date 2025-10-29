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
import pytz

# --- GLOBAL CONFIGURATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_IDS = os.getenv('GROUP_CHAT_IDS', '').split(',')
REGISTER_LINK = os.getenv('REGISTER_LINK', 'https://lkpq.cc/eec3')
CURRENCY_SYMBOL = os.getenv('CURRENCY_SYMBOL', '$')  # Default to USD for global
PORT = int(os.getenv('PORT', 5000))
# --- END CONFIG ---

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Validation
if not BOT_TOKEN:
    logger.error("BOT_TOKEN missing!")
    exit(1)
if not GROUP_CHAT_IDS or not any(GROUP_CHAT_IDS):
    logger.error("No GROUP_CHAT_IDS!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# === GLOBAL PEAK ENGAGEMENT WINDOWS (UTC) ===
# Based on 1win global traffic: India, Brazil, CIS, Turkey, Africa, SEA
GLOBAL_PEAK_WINDOWS_UTC = [
    ("05:35", "06:00"),  # 11:05 IST (India morning)
    ("08:40", "09:05"),  # 14:10 IST (India lunch) / 10:10 TRT (Turkey)
    ("09:50", "10:15"),  # 15:20 IST / 11:20 TRT / 13:20 MSK
    ("13:40", "14:05"),  # 19:10 IST (India prime) / 15:10 TRT / 17:10 MSK
    ("15:55", "16:20"),  # 21:25 IST (India night) / 23:25 MSK / 03:25 BRT (Brazil)
    ("18:45", "19:10"),  # 00:15 IST (Midnight India) / 06:15 BRT / 20:15 TRT
]

# === CURRENCY & LOCALIZATION MAP ===
CURRENCY_MAP = {
    "Asia/Kolkata": "₹",
    "Europe/Moscow": "₽",
    "Europe/Istanbul": "₺",
    "America/Sao_Paulo": "$",
    "Africa/Lagos": "₦",
    "Asia/Jakarta": "Rp",
    "default": "$"
}

# === TEMPLATES (Global, High-Conversion, Urgency-Driven) ===

HYPE_TEMPLATE = """GLOBAL ALERT: LUCKY JET ASCENT DETECTED

AI flagged **{multiplier_preview}x surge** in next 25 mins.

**Only 100 elite global seats** open across 1win network.

**Live online:** {online_count}+ warriors  
**Deposits surging:** {deposits_live} in 10 mins

**T-20 mins** to signal drop. Position now.

[CLAIM 500% BONUS WORLDWIDE]({register_link})
[DEPOSIT & SECURE SEAT]({register_link})

DM @DOREN99 — "GLOBAL IN" for priority."""
    
SIGNAL_TEMPLATE = """ELITE GLOBAL LUCKY JET SIGNAL

**Bet NOW:** {bet_time_local}
**Target Cashout:** {multiplier}x

**Live Proof:** Last 3 → 6.1x | 8.7x | **12.9x**
**1win Global RTP:** 97.6% this hour (verified)

**Seats left:** 23 / 100

{currency_symbol}50 → {currency_symbol}3,000+ with 500% bonus.

[DEPOSIT & EXECUTE]({register_link})

**Global winners act. Others watch.**

DM @DOREN99: "EXECUTED" → Next signal **FREE**."""

SUCCESS_TEMPLATE = """GLOBAL SIGNAL CRUSHED: +{multiplier}x

**Network Profit:** {currency_symbol}{profit:,}+  
**Top Global Winner:** {currency_symbol}5,000 → {currency_symbol}67,000

**Next surge:** T-45 mins. **High volatility window active.**

**Missed?** Avg user lost {currency_symbol}4,200 profit.

[DEPOSIT NOW – JOIN GLOBAL 1%]({register_link})

**Trend:** Multipliers climbing globally. Next = **14x+**

DM @DOREN99: "NEXT" → Reserve seat."""

# === UTILS ===

def get_local_time(utc_dt, timezone_str):
    try:
        tz = ZoneInfo(timezone_str)
        return utc_dt.astimezone(tz)
    except:
        return utc_dt  # Fallback

def detect_user_timezone(chat_id):
    """Simulate timezone detection via chat language or known group"""
    # In real bot: use user language + group metadata
    # For now: cycle through major zones
    zones = ["Asia/Kolkata", "Europe/Moscow", "Europe/Istanbul", "America/Sao_Paulo", "Africa/Lagos"]
    return random.choice(zones)

def get_currency(timezone):
    return CURRENCY_MAP.get(timezone, CURRENCY_MAP["default"])

def random_high_multiplier():
    return round(random.uniform(6.0, 16.0), 2)

def random_profit():
    return random.randint(50000, 300000) // 1000 * 1000

async def get_global_engagement():
    total_members = 0
    for chat_id in GROUP_CHAT_IDS:
        try:
            chat = await bot.get_chat(chat_id.strip())
            total_members += chat.get_members_count() or 0
        except:
            pass
    online = int(total_members * random.uniform(0.12, 0.28)) + random.randint(80, 400)
    deposits = random.randint(35, 120)
    return max(online, 200), deposits  # Global threshold

async def send_to_all(message_func):
    for chat_id in GROUP_CHAT_IDS:
        if not chat_id.strip(): continue
        try:
            await message_func(chat_id.strip())
            await asyncio.sleep(1)
        except TelegramError as e:
            logger.error(f"Send error {chat_id}: {e}")

# === CORE ENGINE ===

async def main():
    logger.info("GLOBAL DYNAMIC ENGINE LIVE: Targeting $3,000+ daily across 5 continents.")
    print("Worldwide profit missile active. 6x global signals/day.")

    deployed_today = set()

    while True:
        try:
            utc_now = datetime.now(pytz.UTC)
            today_str = utc_now.date().isoformat()

            if utc_now.hour == 0 and utc_now.minute < 5:
                deployed_today.clear()

            for idx, (hype_str, bet_str) in enumerate(GLOBAL_PEAK_WINDOWS_UTC):
                if idx in deployed_today:
                    continue

                hype_time = datetime.strptime(f"{today_str} {hype_str}", "%Y-%m-%d %H:%M").replace(tzinfo=pytz.UTC)
                bet_time = datetime.strptime(f"{today_str} {bet_str}", "%Y-%m-%d %H:%M").replace(tzinfo=pytz.UTC)
                success_time = bet_time + timedelta(minutes=5)

                if utc_now > success_time:
                    continue

                # HYPE
                if abs((utc_now - hype_time).total_seconds()) <= 60:
                    online, deposits = await get_global_engagement()
                    if online > 200:
                        mult = random_high_multiplier()
                        logger.info(f"Global Hype #{idx} @ {hype_time}")
                        await send_to_all(lambda cid: bot.send_message(
                            chat_id=cid,
                            text=HYPE_TEMPLATE.format(
                                multiplier_preview=mult,
                                online_count=online,
                                deposits_live=deposits,
                                register_link=REGISTER_LINK
                            ),
                            parse_mode='Markdown',
                            disable_web_page_preview=True
                        ))
                        await asyncio.sleep(60)

                # SIGNAL
                elif abs((utc_now - bet_time).total_seconds()) <= 60:
                    online, _ = await get_global_engagement()
                    if online > 200 and idx not in deployed_today:
                        mult = random_high_multiplier()
                        last_mult = mult
                        # Localize per group (simulate)
                        async def send_local_signal(cid):
                            tz = detect_user_timezone(cid)
                            local_bet = get_local_time(bet_time, tz)
                            curr = get_currency(tz)
                            await bot.send_message(
                                chat_id=cid,
                                text=SIGNAL_TEMPLATE.format(
                                    bet_time_local=local_bet.strftime("%I:%M %p"),
                                    multiplier=mult,
                                    currency_symbol=curr,
                                    register_link=REGISTER_LINK
                                ),
                                parse_mode='Markdown',
                                disable_web_page_preview=True
                            )
                        logger.info(f"Global Signal #{idx} @ {bet_time}")
                        await send_to_all(send_local_signal)
                        deployed_today.add(idx)
                        await asyncio.sleep(60)

                # SUCCESS
                elif abs((utc_now - success_time).total_seconds()) <= 60 and idx in deployed_today:
                    profit = random_profit()
                    async def send_local_success(cid):
                        tz = detect_user_timezone(cid)
                        curr = get_currency(tz)
                        await bot.send_message(
                            chat_id=cid,
                            text=SUCCESS_TEMPLATE.format(
                                multiplier=last_mult,
                                profit=profit,
                                currency_symbol=curr,
                                register_link=REGISTER_LINK
                            ),
                            parse_mode='Markdown',
                            disable_web_page_preview=True
                        )
                    logger.info(f"Global Success #{idx}")
                    await send_to_all(send_local_success)
                    await asyncio.sleep(300)

            await asyncio.sleep(30 if len(deployed_today) < 6 else 3600)

        except Exception as e:
            logger.error(f"Global engine error: {e}")
            await asyncio.sleep(60)

@app.route('/health')
def health_check():
    return jsonify({
        "status": "GLOBAL DOMINATION",
        "target": "$3,000+ daily",
        "coverage": "India • Russia • Turkey • Brazil • Africa • SEA"
    })

def run_bot():
    asyncio.run(main())

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    app.run(host='0.0.0.0', port=PORT)
