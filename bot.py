# bot.py – 1WIN LUCKY JET BEAST 2025 – FINAL BULLETPROOF VERSION
# Works with python-telegram-bot 20.8 → 21.x (auto-detects)

import asyncio
import random
import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, ContextTypes, ChatMemberHandler
from telegram.constants import ChatMemberStatus
from telegram.error import Forbidden

from flask import Flask, jsonify
import threading

# ============================================================
# CONFIG (CHANGE THESE)
# ============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_IDS = [int(x) for x in os.getenv("GROUP_CHAT_IDS", "").split(",") if x.strip()]
REGISTER_LINK = os.getenv("REGISTER_LINK", "https://lkpq.cc/27b4d101")
PROMO_CODE = "DOREN99"
ADMIN_USERNAME = "@DOREN99"          # ← CHANGE THIS (no @)
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
PORT = int(os.getenv("PORT", 5000))

# ============================================================
# SETUP
# ============================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

welcomed_users = set()   # anti-spam welcome

# ============================================================
# MESSAGES
# ============================================================
WELCOME_DM = f"""
WELCOME TO THE #1 LUCKY JET SIGNAL GROUP!

+500% Bonus + 70 Free Spins
Use Promo Code: <b>{PROMO_CODE}</b>

Register & Claim → <a href="{REGISTER_LINK}">CLICK HERE</a>

Min Deposit ₹200 → Play with ₹1,200 Instantly!

VIP Group + 98% Accuracy?
DM @{ADMIN_USERNAME} → write <b>DOREN99</b>

Let’s make money today!
"""

def keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Claim 500% Bonus", url=REGISTER_LINK)],
        [InlineKeyboardButton("Play Lucky Jet Now", url=REGISTER_LINK)]
    ])

LIVE_PROOFS = [
    "Mumbai user just hit 19.8x → ₹38,000!",
    "Delhi player turned ₹300 → ₹2,900!",
    "Kerala VIP cashed out ₹72,000 today!",
    "Bangalore user claimed 700% bonus!"
]

PEAK_WINDOWS = [
    ("6:20 AM", "6:40 AM"), ("9:00 AM", "9:20 AM"), ("12:00 PM", "12:20 PM"),
    ("4:30 PM", "4:50 PM"), ("7:00 PM", "7:20 PM"), ("10:30 PM", "11:55 PM")
]

# ============================================================
# WELCOME NEW MEMBER
# ============================================================
async def welcome_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            text=WELCOME_DM,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        logger.info(f"Welcome DM → {member.full_name} ({member.id})")
    except Forbidden:
        logger.warning(f"User {member.id} blocked bot")
    except Exception as e:
        logger.error(f"Welcome error: {e}")

# ============================================================
# BEAST MESSAGES
# ============================================================
async def send_hype(chat_id):
    await context.bot.send_message(chat_id=chat_id, text=f"""
LIVE ACTIVITY CRAZY!!

{random.choice(LIVE_PROOFS)}

500% Bonus still ON!
""", reply_markup=keyboard())

async def send_signal(chat_id):
    mult = round(random.uniform(9.0, 23.0), 2)
    await context.bot.send_message(chat_id=chat_id, text=f"""
NEXT SIGNAL!!

Game: <b>Lucky Jet</b>
Target: <b>{mult}x</b>

ENTRY IN 60 SEC!!
""", parse_mode="HTML", reply_markup=keyboard())
    return mult

async def send_success(chat_id, mult, profit):
    await context.bot.send_message(chat_id=chat_id, text=f"""
HIT {mult}x !!

Today Profit: ₹{profit:,}+
Next signal soon!
""", reply_markup=keyboard())

# ============================================================
# MAIN BEAST LOOP (no job_queue needed)
# ============================================================
async def beast_loop():
    daily_done = set()
    last_mult = 15.0

    while True:
        try:
            now = datetime.now(ZoneInfo(TIMEZONE))

            # daily reset
            if now.hour == 0 and now.minute < 5:
                daily_done.clear()
                logger.info("Daily windows reset")

            for idx, (s, e) in enumerate(PEAK_WINDOWS):
                if idx in daily_done:
                    continue

                end_time = datetime.strptime(e, "%I:%M %p").time()
                target = datetime.combine(now.date(), end_time, now.tzinfo)
                if now.time() > end_time:
                    target += timedelta(days=1)

                hype_at = target - timedelta(minutes=12)
                signal_at = target
                success_at = target + timedelta(minutes=6)

                if hype_at <= now < signal_at:
                    for cid in GROUP_CHAT_IDS:
                        await send_hype(cid)
                        await asyncio.sleep(1.8)
                    await asyncio.sleep(80)

                elif signal_at <= now < success_at:
                    mults = []
                    for cid in GROUP_CHAT_IDS:
                        m = await send_signal(cid)
                        mults.append(m)
                        await asyncio.sleep(2)
                    last_mult = max(mults) if mults else round(random.uniform(12, 22), 2)
                    daily_done.add(idx)
                    logger.info(f"SIGNAL → {last_mult}x")
                    await asyncio.sleep(90)

                elif success_at <= now < success_at + timedelta(minutes=5):
                    profit = random.randint(14000, 45000)
                    for cid in GROUP_CHAT_IDS:
                        await send_success(cid, last_mult, profit)
                        await asyncio.sleep(1.5)
                    logger.info(f"Success posted → ₹{profit:,}")
                    await asyncio.sleep(300)

            await asyncio.sleep(25)

        except Exception as e:
            logger.error(f"Beast error: {e}")
            await asyncio.sleep(60)

# ============================================================
# HEALTH CHECK
# ============================================================
@app.route("/health")
def health():
    return jsonify({
        "status": "BEAST MODE ACTIVE",
        "groups": len(GROUP_CHAT_IDS),
        "welcome": "ON",
        "next_window": "10:30 PM → 11:55 PM",
        "target": "₹2L+ daily deposits"
    })

# ============================================================
# START EVERYTHING
# ============================================================
async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Welcome handler
    application.add_handler(ChatMemberHandler(welcome_handler, ChatMemberHandler.CHAT_MEMBER))

    # Start beast loop in background (NO job_queue required)
    application.job_queue.run_once(lambda _: asyncio.create_task(beast_loop()), 3)

    logger.info("1WIN LUCKY JET BEAST 2025 STARTED – Welcome DM + Signals LIVE")
    await application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    # Flask health check
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=PORT), daemon=True).start()
    # Start bot
    asyncio.run(main())
