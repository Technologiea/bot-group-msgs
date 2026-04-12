import asyncio
import random
import logging
import os
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from flask import Flask, request
import threading

# ========================= CONFIG =========================
BOT_TOKEN = os.getenv('BOT_TOKEN')
# Add IDs as a comma-separated list in Render Env Vars
GROUP_CHAT_IDS = [int(x.strip()) for x in os.getenv('GROUP_CHAT_IDS', '').split(',') if x.strip()]
REGISTER_LINK = "https://one-vv947.com/?open=register&p=v91c"
PROMOCODE = "BETWIN190"
TIMEZONE_IST = "Asia/Kolkata"
PORT = int(os.getenv('PORT', 10000)) 
APK_FILE_NAME = "1win .apk" 

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)
ist = ZoneInfo(TIMEZONE_IST)

# ========================= KEYBOARDS =========================
def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 REGISTER & GET 500% BONUS", url=REGISTER_LINK)],
        [InlineKeyboardButton("💳 DEPOSIT NOW (VIP ACCESS)", url=REGISTER_LINK)],
        [InlineKeyboardButton("📱 DOWNLOAD ANTI-LAG APP", url=REGISTER_LINK)]
    ])

# ========================= POSTBACK & WEBHOOK =========================

@app.route('/postback', methods=['GET'])
def postback_listener():
    """
    URL for Dashboard: https://bot-group-msgs-xpck.onrender.com/postback?event_name={event_name}&amount={sum}&uid={source_id}
    """
    event = request.args.get('event_name', 'registration')
    amount = request.args.get('amount', '0')
    uid = request.args.get('uid', 'User')

    # Build the shoutout message based on event
    if event in ['first_deposit', 'deposit', 'revenue']:
        msg = (
            f"💰 **NEW VIP DEPOSIT DETECTED!** 💰\n\n"
            f"👤 **Player:** ID_{uid[-4:]}***\n"
            f"💵 **Amount:** ₹{amount}\n"
            f"⚡ **Status:** High-Speed Signals Active ✅\n\n"
            f"*Copy this player's success. Deposit now to join the Power Hour!*"
        )
        send_sync_message(msg)
    
    elif event == 'registration':
        msg = f"🆕 **NEW REGISTRATION!**\nUser ID_{uid[-4:]}*** just joined using code `{PROMOCODE}`! Welcome to the winning circle. 🥂"
        send_sync_message(msg)

    return "OK", 200

def send_sync_message(text):
    """Helper to send messages outside the async loop for Postbacks"""
    for chat_id in GROUP_CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "reply_markup": get_main_keyboard().to_json()}
            requests.post(url, json=payload)
        except Exception as e:
            logger.error(f"Sync send failed: {e}")

# ========================= SIGNAL MESSAGES =========================

ALERT_MSG = """⚠️ **ALGORITHM SCANNING...** ⚠️

⏰ **Signal Time:** {signal_time} IST
🎯 **Confidence:** 98.4%
🔥 **VIP SLOTS LEFT:** {slots} 

✅ Status: **Waiting for Multiplier Peak**
💎 Use Promo Code: `{promocode}`

*New users: Download the APK below for zero-lag execution.* 👇"""

LIVE_MSG = """🔔 **LIVE SIGNAL - BET NOW!** 🔔

🎮 **Game:** AVIATOR
⏰ **Time:** {signal_time} IST
🎯 **AUTO-CASHOUT AT:** **{target}x**

💰 **PROJECTION:**
• ₹1,000 ➡️ **₹{p1}**
• ₹5,000 ➡️ **₹{p5}**
• ₹10,000 ➡️ **₹{p10}** (VIP)

⏳ **Action:** Open App. Place bet. Cashout at {target}x!"""

# ========================= CORE SCHEDULER =========================

async def broadcast(message):
    for chat_id in GROUP_CHAT_IDS:
        try:
            await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown", reply_markup=get_main_keyboard(), disable_web_page_preview=True)
        except Exception as e:
            logger.error(f"Broadcast failed: {e}")

async def signal_scheduler():
    while True:
        now = datetime.now(ist)
        # Active: 10:00 AM to 02:00 AM IST
        if not (10 <= now.hour or now.hour < 2):
            await asyncio.sleep(60)
            continue

        # Signal every 15 or 20 mins
        interval = random.choice([15, 20])
        next_mark = ((now.minute // interval) + 1) * interval
        signal_dt = now.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=next_mark)
        
        # 1. ALERT (5m before)
        wait_alert = (signal_dt - timedelta(minutes=5) - now).total_seconds()
        if wait_alert > 0:
            await asyncio.sleep(wait_alert)
        
        target = round(random.uniform(2.1, 4.9), 2)
        await broadcast(ALERT_MSG.format(signal_time=signal_dt.strftime("%I:%M %p"), slots=random.randint(4, 12), promocode=PROMOCODE))

        # 2. LIVE
        wait_live = (signal_dt - datetime.now(ist)).total_seconds()
        if wait_live > 0: await asyncio.sleep(wait_live)
            
        await broadcast(LIVE_MSG.format(
            signal_time=signal_dt.strftime("%I:%M %p"), 
            target=target,
            p1=f"{int(1000*target):,}", p5=f"{int(5000*target):,}", p10=f"{int(10000*target):,}"
        ))

        # 3. SUCCESS (2m after)
        await asyncio.sleep(120)
        await broadcast(f"✅ **{target}x SMASHED!!** ✅\n\nProfit confirmed. The algorithm wins again! Send winning screenshots to Admin! 💸")

        await asyncio.sleep(600)

# ========================= DEPLOYMENT =========================

@app.route('/')
def health(): return "Aviator Profit Engine Online", 200

def run_async():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(signal_scheduler())

if __name__ == "__main__":
    threading.Thread(target=run_async, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
