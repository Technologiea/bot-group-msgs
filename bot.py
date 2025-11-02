import asyncio
import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import TelegramError
from flask import Flask

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_TELEGRAM_BOT_TOKEN_HERE')
GROUP_CHAT_IDS = os.getenv('GROUP_CHAT_IDS', '').split(',')
REGISTER_LINK = "https://1wyvrz.life/?open=register&p=v91c"
APP_LINK = "https://drive.google.com/file/d/1RDyUaS8JT8RRsMpfTn9Dk7drdiK3MyCW/view?usp=sharing"

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LuckyJetBot")

# --- FLASK SERVER (keep_alive) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "LUCKY JET BOT is running successfully ✅"

# --- TELEGRAM SETUP ---
bot = Bot(token=BOT_TOKEN)

# --- MESSAGE FUNCTIONS ---

async def send_promo_message(chat_id, message_text):
    """Send a promotional message with inline buttons"""
    try:
        buttons = [
            [InlineKeyboardButton("🎯 Register Now", url=REGISTER_LINK)],
            [InlineKeyboardButton("📲 Download App", url=APP_LINK)],
            [InlineKeyboardButton("💰 Deposit Bonus", url=REGISTER_LINK)]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await bot.send_message(
            chat_id=chat_id,
            text=message_text,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        logger.info(f"Message sent to group: {chat_id}")
    except TelegramError as e:
        logger.error(f"Failed to send to {chat_id}: {e}")


async def broadcast_to_groups(message_text):
    """Broadcast message to all configured groups"""
    for chat_id in GROUP_CHAT_IDS:
        chat_id = chat_id.strip()
        if not chat_id:
            continue
        await send_promo_message(chat_id, message_text)
        await asyncio.sleep(1.5)


# --- MAIN LOOP ---
async def main_loop():
    ist = ZoneInfo("Asia/Kolkata")
    while True:
        now = datetime.now(ist)

        # Example promo message (you can edit this anytime)
        message_text = (
            "🔥 LUCKY JET BIG WIN ALERT! 🔥\n\n"
            "Play Lucky Jet now and claim your exclusive bonus using promo code **BETWIN190**.\n"
            "🚀 Fly high, cash out smart, and double your luck!\n\n"
            "👇 Click below to start winning now 👇"
        )

        await broadcast_to_groups(message_text)
        logger.info(f"Broadcast sent at {now.strftime('%Y-%m-%d %H:%M:%S')}")

        # Sleep 3 hours between messages (adjust as needed)
        await asyncio.sleep(3 * 60 * 60)


# --- STARTUP ---
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

if __name__ == "__main__":
    from threading import Thread
    Thread(target=run_flask, daemon=True).start()
    asyncio.run(main_loop())
