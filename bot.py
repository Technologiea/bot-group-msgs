import asyncio
import random
import logging
import os
import requests
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

# ========================= CONFIG =========================
BOT_TOKEN = os.getenv('BOT_TOKEN')
# Add your Group IDs as a comma-separated list in Render (e.g., -100123,-100456)
raw_ids = os.getenv('GROUP_CHAT_IDS', '')
GROUP_CHAT_IDS = [int(x.strip()) for x in raw_ids.split(',') if x.strip()]

REGISTER_LINK = "https://one-vv947.com/?open=register&p=v91c"
PROMOCODE = "BETWIN190"
TIMEZONE_IST = "Asia/Kolkata"
PORT = int(os.getenv('PORT', 10000))

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

# Essential for Gunicorn: Define 'app' at the top level
app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
ist = ZoneInfo(TIMEZONE_IST)

def get_btn():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🚀 DEPOSIT & START WINNING", url=REGISTER_LINK)]])

# ========================= POSTBACK SYSTEM =========================

@app.route('/postback', methods=['GET'])
def postback():
    """
    Dashboard Link: https://bot-group-msgs-xpck.onrender.com/postback?event={event_name}&amt={amount}&uid={user_id}
    """
    event = request.args.get('event')
    uid = request.args.get('uid', 'VIP_Player')
    amt = request.args.get('amt', '0')

    if event in ['registration', 'reg']:
        msg = f"🆕 **NEW REGISTRATION!**\nUser ID: `{uid}` just joined the team using code `{PROMOCODE}`! 🥂"
        send_to_telegram(msg)
    
    elif event in ['deposit', 'first_deposit', 'dep']:
        msg = (
            f"💰 **LIVE DEPOSIT RECEIVED!** 💰\n\n"
            f"👤 **Player:** `{uid}`\n"
            f"💵 **Amount:** ₹{amt}\n"
            f"💎 **Status:** VIP Signal Sync Active ✅\n\n"
            f"*Don't watch others win. Deposit now and follow the next signal!*"
        )
        send_to_telegram(msg)

    return "OK", 200

def send_to_telegram(text):
    for chat_id in GROUP_CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "reply_markup": get_btn().to_json()
            }
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            logger.error(f"Sync postback send failed: {e}")

# ========================= AUTOMATED SIGNALS =========================

async def signal_loop():
    logger.info("Aviator Signal Engine Started...")
    while True:
        try:
            now = datetime.now(ist)
            # Active Window: 10:00 AM to 01:00 AM IST
            if 10 <= now.hour or now.hour < 1:
                target = round(random.uniform(2.15, 4.85), 2)
                sig_time = (now + timedelta(minutes=3)).strftime("%I:%M %p")

                # 1. ALERT (FOMO)
                for cid in GROUP_CHAT_IDS:
                    try:
                        await bot.send_message(
                            chat_id=cid, 
                            text=f"⚠️ **SIGNAL SCANNING...**\n⏰ **Time:** {sig_time} IST\n🔥 **VIP Slots Remaining:** {random.randint(3,8)}\n\n*Ensure your balance is ready for the flight!*",
                            reply_markup=get_btn()
                        )
                    except: pass
                
                await asyncio.sleep(180) # 3 min wait

                # 2. LIVE SIGNAL
                p1000 = int(1000 * target)
                p5000 = int(5000 * target)
                for cid in GROUP_CHAT_IDS:
                    try:
                        await bot.send_message(
                            chat_id=cid, 
                            text=f"🚀 **LIVE SIGNAL: {target}x**\n\n💰 ₹1,000 ➡️ ₹{p1000:,}\n💰 ₹5,000 ➡️ ₹{p5000:,}\n\n*Action: Cashout exactly at {target}x!*",
                            reply_markup=get_btn()
                        )
                    except: pass
                
                # Wait 15-20 mins for next signal
                await asyncio.sleep(random.randint(900, 1200)) 
            else:
                await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Loop error: {e}")
            await asyncio.sleep(10)

# ========================= RENDER STARTUP =========================

@app.route('/')
def health():
    return "Aviator Profit Bot Online", 200

def run_bot_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(signal_loop())

# Crucial: Prevent Gunicorn from starting the bot thread multiple times
if not any(t.name == "BotThread" for t in threading.enumerate()):
    threading.Thread(target=run_bot_thread, daemon=True, name="BotThread").start()

if __name__ == "__main__":
    # Local testing command: python bot.py
    app.run(host='0.0.0.0', port=PORT)
