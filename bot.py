import asyncio
import random
import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, ContextTypes, ChatMemberHandler  # v21: No separate ApplicationBuilder
from telegram.constants import ChatMemberStatus
from telegram.error import Forbidden, TelegramError

from flask import Flask, jsonify
import threading

# ============================================================
# CONFIGURATION - UPDATE THESE
# ============================================================
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_IDS = [int(x.strip()) for x in os.getenv('GROUP_CHAT_IDS', '').split(',') if x.strip()]
REGISTER_LINK = os.getenv('REGISTER_LINK', 'https://lkpq.cc/27b4d101')
PROMO_CODE = "DOREN99"
ADMIN_USERNAME = "youradmin"  # Change to your real username without @
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Kolkata')
PORT = int(os.getenv('PORT', 5000))
ENGAGEMENT_THRESHOLD = 100

# ============================================================
# SETUP
# ============================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)

# Track users who already received welcome (avoid spam)
welcomed_users = set()

# ============================================================
# PEAK WINDOWS (IST)
# ============================================================
PEAK_WINDOWS = [
    ("6:20 AM", "6:40 AM"),
    ("9:00 AM", "9:20 AM"),
    ("12:00 PM", "12:20 PM"),
    ("4:30 PM", "4:50 PM"),
    ("7:00 PM", "7:20 PM"),
    ("10:30 PM", "11:55 PM"),
]

BONUS_OFFERS = [
    "500% Welcome Bonus", "600% Mega Bonus", "700% VIP Bonus", "500% + 70 Free Spins"
]
LIVE_DEPOSITS = [
    "Mumbai user just deposited ₹500 → Playing ₹3,000!",
    "Delhi player claimed 700% bonus → Playing ₹800!",
    "Hyderabad user won ₹4,200 in 2 mins!",
    "Bangalore VIP just cashed out ₹12,400!",
    "Kerala player hit 17.5x → ₹18,000 profit!"
]

# ============================================================
# WELCOME MESSAGE (Sent in Private DM)
# ============================================================
WELCOME_MESSAGE = f"""
🔥 WELCOME TO THE WINNING FAMILY! 🔥

You just joined the most accurate Lucky Jet signal group in India!

💰 Get +500% Bonus on Your First Deposit
   Use Promo Code: <b>{PROMO_CODE}</b>

🎯 Register Now → <a href="{REGISTER_LINK}">Click Here to Claim Bonus</a>

✅ Minimum Deposit ₹200 → Play with ₹1,200 Instantly!
   Many users already made ₹15,000–₹50,000 today!

💎 Want VIP Group + 95% Accuracy + Personal Manager?
   → Message @{ADMIN_USERNAME} and type: <b>DOREN99</b>

See you on the moon! 🚀
"""

def get_signal_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Claim 500% Bonus Now", url=REGISTER_LINK)],
        [InlineKeyboardButton("🎰 Play Lucky Jet Instantly", url=REGISTER_LINK)],
    ])

# ============================================================
# NEW USER JOIN DETECTION + WELCOME DM
# ============================================================
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_member = update.chat_member.new_chat_member.user
    chat = update.chat_member.chat

    # Only care about real users joining our monitored groups
    if chat.id not in GROUP_CHAT_IDS or new_member.is_bot:
        return

    if update.chat_member.new_chat_member.status not in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR):
        return  # not actually joined

    user_id = new_member.id
    if user_id in welcomed_users:
        return  # already welcomed

    welcomed_users.add(user_id)

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=WELCOME_MESSAGE,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        logger.info(f"Welcome DM sent to {new_member.full_name} ({user_id})")
        
        # Optional: Announce in group (uncomment if you want)
        # await context.bot.send_message(chat.id, f"Welcome {new_member.first_name}! Check your DM 🚀")

    except Forbidden:
        logger.warning(f"User {user_id} blocked the bot or never started it")
    except Exception as e:
        logger.error(f"Failed to send welcome to {user_id}: {e}")

# ============================================================
# YOUR BEAST MODE MESSAGES (Hype / Signal / Success)
# ============================================================
async def send_hype(chat_id):
    bonus = random.choice(BONUS_OFFERS)
    live = random.choice(LIVE_DEPOSITS)
    text = f"""
🔥 LIVE ACTIVITY IS CRAZY RIGHT NOW!

{live}
{bonus} still active!

👇 Players are depositing & winning non-stop!
"""
    try:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=get_signal_keyboard())
    except Exception as e:
        logger.error(f"Hype failed in {chat_id}: {e}")

async def send_signal(chat_id):
    multiplier = round(random.uniform(8.0, 19.0), 2)
    text = f"""
🚀 NEXT SIGNAL IS READY!

Game: <b>Lucky Jet</b>
Bet in next 60 seconds
Target: <b>{multiplier}x</b>

<b>ENTRY NOW!</b> Don't miss this one!
"""
    msg = await bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode='HTML',
        reply_markup=get_signal_keyboard()
    )
    return multiplier

async def send_success(chat_id, multi, profit):
    text = f"""
✅ SIGNAL HIT {multi}x !!

💰 Total Profit Today: ₹{profit:,}+
Another winner added to the list!

Next signal in 10–15 mins 🔥
"""
    await bot.send_message(chat_id=chat_id, text=text, reply_markup=get_signal_keyboard())

# ============================================================
# MAIN BEAST LOOP (Unchanged logic, just cleaned)
# ============================================================
async def beast_loop():
    daily_done = set()
    last_mult = 12.5

    while True:
        try:
            now = datetime.now(ZoneInfo(TIMEZONE))
            if now.hour == 0 and now.minute < 5:
                daily_done.clear()

            for i, (start, end) in enumerate(PEAK_WINDOWS):
                if i in daily_done:
                    continue

                end_time = datetime.strptime(end, "%I:%M %p").time()
                target_dt = datetime.combine(now.date(), end_time, now.tzinfo)
                if now.time() > end_time:
                    target_dt += timedelta(days=1)

                hype_time = target_dt - timedelta(minutes=12)
                signal_time = target_dt
                success_time = target_dt + timedelta(minutes=6)

                if abs((now - hype_time).total_seconds()) < 120:
                    await asyncio.gather(*(send_hype(cid) for cid in GROUP_CHAT_IDS))
                    await asyncio.sleep(90)

                elif abs((now - signal_time).total_seconds()) < 120:
                    results = await asyncio.gather(*(send_signal(cid) for cid in GROUP_CHAT_IDS), return_exceptions=True)
                    last_mult = next((r for r in results if isinstance(r, float)), random.uniform(10, 18))
                    daily_done.add(i)
                    logger.info(f"SIGNAL SENT → {last_mult}x")
                    await asyncio.sleep(90)

                elif abs((now - success_time).total_seconds()) < 180 and i in daily_done:
                    profit = random.randint(8000, 25000)
                    await asyncio.gather(*(send_success(cid, last_mult, profit) for cid in GROUP_CHAT_IDS))
                    logger.info(f"Success posted: ₹{profit:,}")
                    await asyncio.sleep(300)

            await asyncio.sleep(45)
        except Exception as e:
            logger.error(f"Beast loop error: {e}")
            await asyncio.sleep(60)

# ============================================================
# HEALTH CHECK
# ============================================================
@app.route('/health')
def health():
    return jsonify({
        "status": "BEAST MODE ACTIVE",
        "groups": len(GROUP_CHAT_IDS),
        "welcome_system": "ON",
        "next_big_window": "10:30 PM → 11:55 PM",
        "target": "₹2L+ daily deposits"
    })

# ============================================================
# MAIN START (v21 compatible)
# ============================================================
async def main():
    # v21: Use Application.builder() directly
    application = Application.builder().token(BOT_TOKEN).build()

    # Add the welcome handler
    application.add_handler(ChatMemberHandler(welcome_new_member, ChatMemberHandler.CHAT_MEMBER))

    # Start beast mode in background (use job_queue for repeating task)
    async def run_beast():
        await beast_loop()

    application.job_queue.run_repeating(run_beast, interval=60, first=10)  # Run every 60s, start after 10s

    logger.info("1WIN LUCKY JET BEAST 2025 STARTED | Welcome DM + Signals ACTIVE")
    await application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    # Run Flask health check in thread
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True).start()
    
    # Start the real bot
    asyncio.run(main())
