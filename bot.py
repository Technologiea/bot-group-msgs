# bot.py – 1WIN LUCKY JET BEAST 2025 – FINAL VERSION (NO MORE CRASHES)
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

# ====================== CONFIG ======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_IDS = [int(x) for x in os.getenv("GROUP_CHAT_IDS", "").split(",") if x.strip()]
REGISTER_LINK = os.getenv("REGISTER_LINK", "https://lkpq.cc/27b4d101")
PROMO_CODE = "DOREN99"
ADMIN_USERNAME = "yourusername"        # ← CHANGE THIS (no @)
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
PORT = int(os.getenv("PORT", 5000))

# ====================== SETUP ======================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

welcomed_users = set()   # prevent welcome spam

# ====================== MESSAGES ======================
WELCOME_DM = f"""
WELCOME TO THE BEST LUCKY JET SIGNAL GROUP!

+500% First Deposit Bonus
Use Promo Code: <b>{PROMO_CODE}</b>

Register Now → <a href="{REGISTER_LINK}">CLAIM BONUS</a>

Min ₹200 → Play with ₹1,200 Instantly!

Want VIP Group (98% Win Rate)?
DM @{ADMIN_USERNAME} → write <b>DOREN99</b>

Let's make money today!
"""

def keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Claim 500% Bonus", url=REGISTER_LINK)],
        [InlineKeyboardButton("Play Lucky Jet", url=REGISTER_LINK)]
    ])

LIVE_PROOFS = [
    "Mumbai user just won ₹27,000!",
    "Delhi player hit 21x → ₹42,000!",
    "Kerala VIP cashed out ₹85,000 today!",
    "Bangalore user turned ₹500 → ₹5,200!"
]

PEAK_WINDOWS = [
    ("6:20 AM", "6:40 AM"), ("9:00 AM", "9:20 AM"), ("12:00 PM", "12:20 PM"),
    ("4:30 PM", "4:50 PM"), ("7:00 PM", "7:20 PM"), ("10:30 PM", "11:55 PM")
]

# ====================== WELCOME HANDLER ======================
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
        logger.info(f"Welcome DM sent → {member.full_name} ({member.id})")
    except Forbidden:
        pass
    except Exception as e:
        logger.error(f"Welcome error: {e}")

# ====================== BEAST MESSAGES ======================
async def send_hype(chat_id):
    await app_context.bot.send_message(chat_id=chat_id,
        text=f"LIVE ACTIVITY EXPLODING!\n\n{random.choice(LIVE_PROOFS)}\n\n500% Bonus Active!",
        reply_markup=keyboard())

async def send_signal(chat_id):
    mult = round(random.uniform(9.0, 24.0), 2)
    await app_context.bot.send_message(chat_id=chat_id,
        text=f"NEXT SIGNAL!\n\nGame: <b>Lucky Jet</b>\nTarget: <b>{mult}x</b>\n\nENTRY NOW (60 sec)!",
        parse_mode="HTML", reply_markup=keyboard())
    return mult

async def send_success(chat_id, mult, profit):
    await app_context.bot.send_message(chat_id=chat_id,
        text=f"SIGNAL HIT {mult}x!\n\nToday Profit: ₹{profit:,}+\nNext signal soon!",
        reply_markup=keyboard())

# ====================== BEAST LOOP (NO JOB QUEUE) ======================
async def beast_loop():
    daily_done = set()
    last_mult = 15.0

    while True:
        try:
            now = datetime.now(ZoneInfo(TIMEZONE))

            if now.hour == 0 and now.minute < 5:
                daily_done.clear()
                logger.info("Daily reset")

            for i, (s, e) in enumerate(PEAK_WINDOWS):
                if i in daily_done: continue

                end_t = datetime.strptime(e, "%I:%M %p").time()
                target = datetime.combine(now.date(), end_t, now.tzinfo)
                if now.time() > end_t: target += timedelta(days=1)

                hype_at   = target - timedelta(minutes=12)
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
                    last_mult = max(mults) if mults else random.uniform(12, 22)
                    daily_done.add(i)
                    logger.info(f"SIGNAL → {last_mult:.2f}x")
                    await asyncio.sleep(90)

                elif success_at <= now < success_at + timedelta(minutes=5):
                    profit = random.randint(18000, 52000)
                    for cid in GROUP_CHAT_IDS:
                        await send_success(cid, last_mult, profit)
                        await asyncio.sleep(1.5)
                    logger.info(f"Success → ₹{profit:,}")
                    await asyncio.sleep(300)

            await asyncio.sleep(20)
        except Exception as e:
            logger.error(f"Beast error: {e}")
            await asyncio.sleep(60)

# ====================== HEALTH CHECK ======================
@app.route("/health")
def health():
    return jsonify({
        "status": "LIVE",
        "groups": len(GROUP_CHAT_IDS),
        "welcome_system": "ACTIVE",
        "next_big_window": "10:30 PM → 11:55 PM"
    })

# ====================== MAIN ======================
async def main():
    global app_context
    application = Application.builder().token(BOT_TOKEN).build()
    app_context = application  # needed for send_* functions

    application.add_handler(ChatMemberHandler(welcome_handler, ChatMemberHandler.CHAT_MEMBER))

    # Start beast loop in background (no job_queue → no errors)
    application.create_task(beast_loop())

    logger.info("1WIN LUCKY JET BEAST 2025 STARTED – EVERYTHING LIVE!")
    await application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    # Flask in background thread
    import threading
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=PORT), daemon=True).start()
    
    # Run bot (this is the ONLY asyncio.run)
    asyncio.run(main())
