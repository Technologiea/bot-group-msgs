import asyncio
import random
import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton, Poll
from telegram.error import TelegramError
from flask import Flask, jsonify
import threading

# ============================================================
# CONFIGURATION
# ============================================================
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_IDS = [x.strip() for x in os.getenv('GROUP_CHAT_IDS', '').split(',') if x.strip()]
REGISTER_LINK = os.getenv('REGISTER_LINK', 'https://lkpq.cc/27b4d101')  # Direct web reg
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Kolkata')
CURRENCY_SYMBOL = os.getenv('CURRENCY_SYMBOL', '₹')
PORT = int(os.getenv('PORT', 5000))
ENGAGEMENT_THRESHOLD = int(os.getenv('ENGAGEMENT_THRESHOLD', '150'))

# ============================================================
# VALIDATION
# ============================================================
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

if not BOT_TOKEN:
    logger.error("BOT_TOKEN is not set!")
    exit(1)
if not GROUP_CHAT_IDS:
    logger.error("No GROUP_CHAT_IDS configured!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# ============================================================
# PEAK WINDOWS (IST)
# ============================================================
PEAK_WINDOWS = [
    ("6:20 AM", "6:40 AM"),
    ("9:00 AM", "9:20 AM"),
    ("12:00 PM", "12:20 PM"),
    ("4:30 PM", "4:50 PM"),
    ("7:00 PM", "7:20 PM"),
    ("10:30 PM", "10:50 PM")
]

# ============================================================
# DYNAMIC BONUS ROTATION
# ============================================================
BONUS_OFFERS = [
    ("500% Welcome Bonus", "Deposit ₹100 → Play ₹600"),
    ("600% Mega Bonus", "Deposit ₹100 → Play ₹700"),
    ("700% VIP Bonus", "Deposit ₹100 → Play ₹800"),
    ("500% + 70 Free Spins", "Instant Play + Spins"),
]

# ============================================================
# SOCIAL PROOF (Live Activity)
# ============================================================
LIVE_DEPOSITS = [
    "Mumbai user just deposited ₹500 → Playing ₹3,000!",
    "Delhi player claimed 700% bonus → ₹800 in play!",
    "Hyderabad user won ₹4,200 in 2 mins!",
    "Bangalore VIP just cashed out ₹12,400!",
    "Kerala player activated 70 free spins!"
]

# ============================================================
# INLINE KEYBOARD (Web Only)
# ============================================================
def get_deposit_keyboard(bonus_text):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f" Claim {bonus_text}", url=REGISTER_LINK)],
        [InlineKeyboardButton(" Play Now – Instant Access", url=REGISTER_LINK)],
    ])

# ============================================================
# MESSAGE TEMPLATES (A/B Variants)
# ============================================================
HYPE_VARIANTS = [
    (
        " *LUCKY JET — NEXT BIG WIN IN 15 MINS!* \n\n"
        "500+ players online \n"
        "Live deposits pouring in! \n\n"
        "{live_proof}\n\n"
        " Claim {bonus} → [Join Now]({link})\n\n"
        "_18+ | Play Responsibly_"
    ),
    (
        " *SIGNAL LOADING… GET READY!* \n\n"
        "Next cashout: *High Multiplier Alert* \n"
        "Last 3 signals: 8.2x | 11.4x | 14.1x \n\n"
        "{live_proof}\n\n"
        " {bonus} → [Join Now]({link})\n\n"
        "_Limited Bonus Slots_"
    )
]

SIGNAL_VARIANTS = [
    (
        " *LIVE SIGNAL — ENTER NOW!* \n\n"
        "Bet: *IMMEDIATELY* \n"
        "Target: *{multi}x CASH OUT* \n\n"
        " {bonus_text}\n"
        " [Join & Play Now]({link})\n\n"
        "_Reply “DONE” after deposit for VIP signals_"
    ),
    (
        " *GO GO GO!* \n\n"
        "Multiplier climbing: *{multi}x* → CASH OUT! \n"
        "100+ players winning live \n\n"
        "{live_proof}\n\n"
        " {bonus_text} → [Claim Now]({link})\n\n"
        "_Last Chance – Bonus Ends Soon!_"
    )
]

SUCCESS_VARIANTS = [
    (
        " *SIGNAL HIT: +{multi}x!* \n\n"
        "Group Profit: *{currency}{profit:,}* \n"
        "Next signal in ~40 mins \n\n"
        "{live_proof}\n\n"
        " [Join & Get Next Signal]({link})\n\n"
        "_18+ | Gamble Responsibly_"
    )
]

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def parse_time_str(t_str: str):
    try:
        return datetime.strptime(t_str, "%I:%M %p").time()
    except:
        return None

def get_bet_time(idx: int):
    t = parse_time_str(PEAK_WINDOWS[idx][1])
    if not t:
        return None
    tz = ZoneInfo(TIMEZONE)
    now = datetime.now(tz)
    dt = datetime.combine(now.date(), t, tzinfo=tz)
    return dt + timedelta(days=1) if now > dt else dt

def random_multiplier():
    return round(random.choice([random.uniform(5.0, 9.0), random.uniform(10.0, 15.0)]), 2)

def random_profit():
    return random.randint(2500, 15000)

def get_random_bonus():
    return random.choice(BONUS_OFFERS)

def get_live_proof():
    return random.choice(LIVE_DEPOSITS)

# ============================================================
# ENGAGEMENT CHECK
# ============================================================
async def get_real_engagement(chat_id: str):
    try:
        chat = await bot.get_chat(chat_id)
        member_count = getattr(chat, 'members_count', 1000)
        online_estimate = max(50, int(member_count * random.uniform(0.10, 0.18)))
        deposits = random.randint(8, 45)
        return online_estimate, deposits
    except:
        return 120, random.randint(12, 40)

# ============================================================
# SENDERS
# ============================================================
async def send_hype(cid):
    bonus_name, bonus_text = get_random_bonus()
    keyboard = get_deposit_keyboard(bonus_name)
    variant = random.choice(HYPE_VARIANTS)
    live = get_live_proof()
    msg = variant.format(
        bonus=bonus_name,
        bonus_text=bonus_text,
        live_proof=live,
        link=REGISTER_LINK,
        currency=CURRENCY_SYMBOL
    )
    await bot.send_message(
        cid, msg, parse_mode="Markdown",
        disable_web_page_preview=True,
        reply_markup=keyboard
    )
    # Add Poll for engagement
    try:
        await bot.send_poll(
            cid,
            " Ready for the next signal?",
            [" Yes, let's win!", " Already deposited!"],
            is_anonymous=False
        )
    except:
        pass

async def send_signal(cid):
    m = random_multiplier()
    bonus_name, bonus_text = get_random_bonus()
    keyboard = get_deposit_keyboard(bonus_name)
    variant = random.choice(SIGNAL_VARIANTS)
    live = get_live_proof()
    msg = variant.format(
        multi=m,
        bonus_text=bonus_text,
        live_proof=live,
        link=REGISTER_LINK
    )
    await bot.send_message(
        cid, msg, parse_mode="Markdown",
        disable_web_page_preview=True,
        reply_markup=keyboard
    )
    return m

async def send_success(cid, m, profit):
    keyboard = get_deposit_keyboard("Next Bonus")
    variant = random.choice(SUCCESS_VARIANTS)
    live = get_live_proof()
    msg = variant.format(
        multi=m,
        profit=profit,
        live_proof=live,
        link=REGISTER_LINK,
        currency=CURRENCY_SYMBOL
    )
    await bot.send_message(
        cid, msg, parse_mode="Markdown",
        disable_web_page_preview=True,
        reply_markup=keyboard
    )

# ============================================================
# MAIN LOOP
# ============================================================
async def main():
    logger.info(" LUCKY JET BEAST MODE 2.0 | NO APK | MAX CONVERSIONS")
    daily_done = set()
    last_mult = 0

    while True:
        try:
            tz = ZoneInfo(TIMEZONE)
            now = datetime.now(tz)

            # Reset at midnight
            if now.hour == 0 and now.minute < 5:
                daily_done.clear()
                logger.info("Daily reset complete.")

            for i in range(len(PEAK_WINDOWS)):
                if i in daily_done:
                    continue

                bt = get_bet_time(i)
                if not bt:
                    continue

                ht = bt - timedelta(minutes=12)  # Hype 12 mins before
                st = bt + timedelta(minutes=6)   # Success 6 mins after

                # HYPE
                if abs((now - ht).total_seconds()) < 90:
                    tasks = []
                    for cid in GROUP_CHAT_IDS:
                        online, _ = await get_real_engagement(cid)
                        if online >= ENGAGEMENT_THRESHOLD:
                            tasks.append(send_hype(cid))
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                        logger.info(f" Hype sent (Window {i+1})")
                        await asyncio.sleep(90)

                # SIGNAL
                elif abs((now - bt).total_seconds()) < 90:
                    tasks = []
                    for cid in GROUP_CHAT_IDS:
                        online, _ = await get_real_engagement(cid)
                        if online >= ENGAGEMENT_THRESHOLD:
                            tasks.append(send_signal(cid))
                    if tasks:
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        last_mult = results[0] if results else random_multiplier()
                        daily_done.add(i)
                        logger.info(f" Signal sent: {last_mult}x")
                        await asyncio.sleep(90)

                # SUCCESS
                elif abs((now - st).total_seconds()) < 120 and i in daily_done:
                    profit = random_profit()
                    tasks = [send_success(cid, last_mult, profit) for cid in GROUP_CHAT_IDS]
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                        logger.info(f" Success sent: +{profit:,}")
                        await asyncio.sleep(300)

            await asyncio.sleep(45 if len(daily_done) < 6 else 3600)

        except Exception as e:
            logger.error(f"ERROR: {e}")
            await asyncio.sleep(60)

# ============================================================
# FLASK HEALTH CHECK
# ============================================================
@app.route('/health')
def health():
    return jsonify({
        "status": "LIVE",
        "bot": "1Win Sales Beast 2.0",
        "mode": "NO_APK_MAX_CONVERSIONS",
        "target": "₹2,00,000+/day",
        "features": [
            "No APK", "Web-Only", "Dynamic Bonuses",
            "FOMO + Social Proof", "A/B Testing",
            "Polls", "Auto-Retry", "Clean & Safe"
        ],
        "timezone": TIMEZONE
    })

# ============================================================
# RUN
# ============================================================
def run_bot():
    asyncio.run(main())

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT, use_reloader=False)
