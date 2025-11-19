# bot.py - 1WIN LUCKY JET BEAST 2025 - FINAL VERSION
# Works on Python 3.12 (recommended) + python-telegram-bot 20.8
# OR Python 3.13 + python-telegram-bot 21.4+

import asyncio
import random
import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, ContextTypes, ChatMemberHandler
from telegram.constants import ChatMemberStatus
from telegram.error import Forbidden, TelegramError

from flask import Flask, jsonify
import threading

# ============================================================
# CONFIGURATION - UPDATE THESE
# ============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_IDS = [int(x) for x in os.getenv("GROUP_CHAT_IDS", "").split(",") if x.strip()]
REGISTER_LINK = os.getenv("REGISTER_LINK", "https://lkpq.cc/27b4d101")
PROMO_CODE = "DOREN99"
ADMIN_USERNAME = "yourusername"  # Change this! (without @)
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
PORT = int(os.getenv("PORT", 5000))

# ============================================================
# SETUP
# ============================================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# To prevent welcome spam
welcomed_users = set()

# ============================================================
# MESSAGES & KEYBOARD
# ============================================================
WELCOME_MESSAGE = f"""
WELCOME TO THE #1 LUCKY JET WINNING GROUP!

+500% First Deposit Bonus Active!
Use Promo Code: <b>{PROMO_CODE}</b>

Register & Claim Now:
<a href="{REGISTER_LINK}">CLICK HERE - GET ₹1,200 FREE</a>

Minimum Deposit ₹200 → Play with ₹1,200 Instantly!

Want VIP Group + 98% Accuracy Signals?
→ DM @{ADMIN_USERNAME} and write: <b>DOREN99</b>

Let's make money today!
"""

def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Claim 500% Bonus Now", url=REGISTER_LINK)],
        [InlineKeyboardButton("Play Lucky Jet Instantly", url=REGISTER_LINK)]
    ])

LIVE_PROOFS = [
    "Mumbai user just won ₹18,400 in 3 mins!",
    "Delhi player claimed 700% bonus → ₹5,000 profit!",
    "Kerala VIP hit 21x → ₹42,000 cashout!",
    "Bangalore user turned ₹500 → ₹4,200!"
]

# ============================================================
# PEAK WINDOWS (IST)
# ============================================================
PEAK_WINDOWS = [
    ("6:20 AM", "6:40 AM"),
    ("9:00 AM", "9:20 AM"),
    ("12:00 PM", "12:20 PM"),
    ("4:30 PM", "4:50 PM"),
    ("7:00 PM", "7:20 PM"),
    ("10:30 PM", "11:55 PM"),  # Extended as you wanted
]

# ============================================================
# WELCOME NEW MEMBER (Private DM)
# ============================================================
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = update.chat_member.new_chat_member.user
    chat_id = update.chat_member.chat.id

    if chat_id not in GROUP_CHAT_IDS or member.is_bot:
        return

    if update.chat_member.new_chat_member.status not in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR):
        return

    if member.id in welcomed_users:
        return

    welcomed_users.add(member.id)

    try:
        await context.bot.send_message(
            chat_id=member.id,
            text=WELCOME_MESSAGE,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        logger.info(f"Welcome DM sent to {member.full_name} ({member.id})")
    except Forbidden:
        logger.warning(f"User {member.id} blocked the bot")
    except Exception as e:
        logger.error(f"Welcome failed: {e}")

# ============================================================
# BEAST MESSAGES
# ============================================================
async def send_hype(chat_id):
    proof = random.choice(LIVE_PROOFS)
    text = f"""
LIVE ACTIVITY EXPLODING RIGHT NOW!!

{proof}

500% Bonus Still Active!
Players depositing & winning non-stop!
"""
    try:
        await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=get_keyboard())
    except: pass

async def send_signal(chat_id):
    mult = round(random.uniform(9.0, 22.0), 2)
    text = f"""
NEXT SIGNAL IS READY!!

Game: <b>Lucky Jet</b>
Target: <b>{mult}x</b>

ENTRY NOW - 60 SECONDS!

Don't miss this rocket!
"""
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="HTML",
        reply_markup=get_keyboard()
    )
    return mult

async def send_success(chat_id, mult, profit):
    text = f"""
SIGNAL HIT {mult}x !!

Total Profit Today: ₹{profit:,}+
Another winner added!

Next signal in 10-15 mins
"""
    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=get_keyboard())

# ============================================================
# MAIN BEAST LOOP
# ============================================================
async def beast_loop():
    daily_done = set()
    last_multiplier = 15.5

    while True:
        try:
            now = datetime.now(ZoneInfo(TIMEZONE))
            current_time = now.time()

            # Reset daily at midnight
            if now.hour == 0 and now.minute < 5:
                daily_done.clear()
                logger.info("Daily windows reset")

            for i, (start_str, end_str) in enumerate(PEAK_WINDOWS):
                if i in daily_done:
                    continue

                end_time = datetime.strptime(end_str, "%I:%M %p").time()
                target = datetime.combine(now.date(), end_time, now.tzinfo)
                if current_time > end_time:
                    target += timedelta(days=1)

                hype_time = target - timedelta(minutes=12)
                signal_time = target
                success_time = target + timedelta(minutes=6)

                # Hype phase
                if hype_time <= now < signal_time:
                    for cid in GROUP_CHAT_IDS:
                        await send_hype(cid)
                        await asyncio.sleep(1.5)  # Anti-flood
                    await asyncio.sleep(80)

                # Signal phase
                elif signal_time <= now < success_time:
                    results = []
                    for cid in GROUP_CHAT_IDS:
                        mult = await send_signal(cid)
                        results.append(mult)
                        await asyncio.sleep(1.8)
                    last_multiplier = max(results) if results else round(random.uniform(12, 20), 2)
                    daily_done.add(i)
                    logger.info(f"SIGNAL FIRED → {last_multiplier}x")
                    await asyncio.sleep(90)

                # Success phase
                elif success_time <= now < success_time + timedelta(minutes=5):
                    profit = random.randint(12000, 38000)
                    for cid in GROUP_CHAT_IDS:
                        await send_success(cid, last_multiplier, profit)
                        await asyncio.sleep(1.5)
                    logger.info(f"Success posted: ₹{profit:,}")
                    await asyncio.sleep(300)

            await asyncio.sleep(30)

        except Exception as e:
            logger.error(f"Beast loop error: {e}")
            await asyncio.sleep(60)

# ============================================================
# HEALTH CHECK
# ============================================================
@app.route("/health")
def health():
    return jsonify({
        "status": "LIVE & ACTIVE",
        "bot": "1Win Lucky Jet Beast 2025",
        "groups": len(GROUP_CHAT_IDS),
        "welcome_system": "ON",
        "next_window": "10:30 PM → 11:55 PM",
        "target": "₹2,00,000+ daily"
    })

# ============================================================
# START BOT
# ============================================================
async def main():
    app_builder = Application.builder().token(BOT_TOKEN)
    application = app_builder.build()

    # Add handlers
    application.add_handler(ChatMemberHandler(welcome_new_member, ChatMemberHandler.CHAT_MEMBER))

    # Start beast loop in background
    application.job_queue.run_once(lambda ctx: asyncio.create_task(beast_loop()), 5)

    logger.info("1WIN LUCKY JET BEAST 2025 STARTED SUCCESSFULLY!")
    logger.info("Welcome DM + Auto Signals ACTIVE")

    await application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == "__main__":
    # Flask health check in background
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=PORT), daemon=True).start()
    
    # Start Telegram bot
    asyncio.run(main())
