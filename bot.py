import asyncio
import random
import logging
import os
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
import threading

# ========================= CONFIG =========================
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_IDS = [int(x.strip()) for x in os.getenv('GROUP_CHAT_IDS', '').split(',') if x.strip()]
REGISTER_LINK = "https://one-vv947.com/?open=register&p=v91c"
PROMOCODE = "BETWIN190"
TIMEZONE_IST = "Asia/Kolkata"
PORT = int(os.getenv('PORT', 10000)) 

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)
ist = ZoneInfo(TIMEZONE_IST)

def get_btn():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🚀 DEPOSIT & START WINNING", url=REGISTER_LINK)]])

# ========================= POSTBACK SYSTEM =========================

@app.route('/postback', methods=['GET'])
def postback():
    # Matching the macros from your screenshot
    event = request.args.get('event')
    uid = request.args.get('uid', 'VIP')
    amt = request.args.get('amt', '0')

    if event == 'reg':
        msg = f"🆕 **NEW REGISTRATION!**\nUser ID: `{uid}` joined the team! Welcome aboard. 🥂"
        send_to_telegram(msg)
    
    elif event == 'dep':
        msg = (
            f"💰 **SUCCESSFUL DEPOSIT!** 💰\n\n"
            f"👤 **Player:** `{uid}`\n"
            f"💵 **Amount:** ₹{amt}\n"
            f"⚡ **Signals:** 100% Synchronized ✅\n\n"
            f"*Check your app now. Let's fly!* 🛫"
        )
        send_to_telegram(msg)

    return "OK", 200

def send_to_telegram(text):
    for chat_id in GROUP_CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "reply_markup": get_btn().to_json()})
        except: pass

# ========================= AUTOMATED SIGNALS =========================

async def signal_loop():
    while True:
        now = datetime.now(ist)
        # 10 AM to 1 AM
        if 10 <= now.hour or now.hour < 1:
            target = round(random.uniform(2.1, 4.9), 2)
            sig_time = (now + timedelta(minutes=3)).strftime("%I:%M %p")

            # ALERT
            for cid in GROUP_CHAT_IDS:
                await bot.send_message(cid, f"⚠️ **PREPARING SIGNAL...**\n⏰ Time: {sig_time}\n🔥 Slots: {random.randint(2,7)} left!", reply_markup=get_btn())
            
            await asyncio.sleep(180) # 3 min wait

            # LIVE
            p1 = int(1000 * target)
            for cid in GROUP_CHAT_IDS:
                await bot.send_message(cid, f"🚀 **LIVE SIGNAL: {target}x**\n\n💰 ₹1,000 -> ₹{p1:,}\n\n*Cashout exactly at {target}x!*", reply_markup=get_btn())
            
            await asyncio.sleep(900) # Next signal in 15 mins
        else:
            await asyncio.sleep(60)

# ========================= START =========================

@app.route('/')
def health(): return "Ready", 200

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(signal_loop())

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
