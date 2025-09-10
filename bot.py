import asyncio
import random
import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram import Bot
from telegram.error import TelegramError
from flask import Flask, jsonify

# Initialize Flask app
app = Flask(__name__)

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_IDS = os.getenv('GROUP_CHAT_IDS', '').split(',')
REGISTER_LINK = os.getenv('REGISTER_LINK', 'https://lkpq.cc/eec3')
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Kolkata')
CURRENCY_SYMBOL = os.getenv('CURRENCY_SYMBOL', '₹')
# --- CONFIGURATION ---

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)

# Enhanced message templates
SIGNAL_TEMPLATES = [
    """🚀 *LUCKYJET SIGNAL ALERT* 🚀

🔥 *Limited Offer:* Get 500% BONUS on your first deposit!

⏰ Bet Time: {bet_time}
🎯 Cash Out Target: {multiplier}x

✨ *Why wait? Your winning moment is now!*

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

⚡ Start with just {currency_symbol}10 and multiply your money!
{reactions}""",

    """🎰 *WINNING SIGNAL CONFIRMED* 🎰

💎 *Special Bonus:* 500% EXTRA on first deposit!

🕒 Recommended Time: {bet_time}
📈 Target Multiplier: {multiplier}x

🌟 *Your journey to big wins starts here!*

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

🚀 Turn {currency_symbol}20 into {currency_symbol}100+ with this signal!
{reactions}"""
]

REGISTER_TEMPLATES = [
    """💎 *READY TO WIN BIG?* 💎

Create your account now and claim your 500% welcome bonus!

✨ *Why choose us?*
✅ Highest success rate signals
✅ Instant withdrawals
✅ 24/7 professional support

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

⚡ Your first big win is just minutes away!
{reactions}""",

    """🎯 *DON'T MISS YOUR OPPORTUNITY!* 🎯

Join thousands of winners who started with our 500% bonus!

🔥 *Limited time offer:*
⭐ 500% welcome bonus
⭐ Daily guaranteed signals
⭐ Professional betting guidance

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

✨ Your future self will thank you!
{reactions}"""
]

# Emoji reactions with specified frequencies
REACTION_WEIGHTS = {
    "🔥": 5,  # 5 times more likely
    "💰": 3,  # 3 times more likely
    "💸": 3,  # 3 times more likely
    "🚀": 2,  # 2 times more likely
    "⭐": 5,  # 5 times more likely
    "💎": 1,  # Standard weight
    "✨": 2   # 2 times more likely
}

def random_multiplier():
    return round(random.uniform(1.5, 12.5), 2)

def random_reactions():
    # Create a weighted list of emojis
    weighted_emojis = []
    for emoji, weight in REACTION_WEIGHTS.items():
        weighted_emojis.extend([emoji] * weight)
    
    # Select 5 random emojis from the weighted list
    selected_emojis = random.sample(weighted_emojis, 5)
    return " ".join(selected_emojis)

def get_bet_time():
    now = datetime.now(ZoneInfo(TIMEZONE))
    bet_time = now + timedelta(minutes=random.randint(3, 8))
    return bet_time.strftime("%I:%M %p")

async def send_to_all_channels(message_func):
    """Helper function to send messages to all channels"""
    for chat_id in GROUP_CHAT_IDS:
        if not chat_id.strip():
            continue
            
        try:
            await message_func(chat_id.strip())
            # Add a small delay between messages to avoid rate limiting
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error sending to {chat_id}: {e}")

async def send_signal_to_chat(chat_id):
    """Send signal to a specific chat"""
    bet_time = get_bet_time()
    multiplier = random_multiplier()
    message = random.choice(SIGNAL_TEMPLATES).format(
        bet_time=bet_time,
        multiplier=multiplier,
        currency_symbol=CURRENCY_SYMBOL,
        register_link=REGISTER_LINK,
        reactions=random_reactions()
    )
    
    await bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
    logger.info(f"Signal sent to {chat_id} for Bet Time {bet_time}")

async def send_register_to_chat(chat_id):
    """Send register message to a specific chat"""
    message = random.choice(REGISTER_TEMPLATES).format(
        currency_symbol=CURRENCY_SYMBOL,
        register_link=REGISTER_LINK,
        reactions=random_reactions()
    )
    
    await bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
    logger.info(f"Register message sent to {chat_id}")

async def send_signal():
    """Send signal to all channels"""
    await send_to_all_channels(send_signal_to_chat)

async def send_register():
    """Send register message to all channels"""
    await send_to_all_channels(send_register_to_chat)

async def main():
    logger.info("Bot started successfully...")
    print("Bot is running. Press Ctrl+C to stop.")
    
    # Validate we have at least one chat ID
    if not GROUP_CHAT_IDS or not any(GROUP_CHAT_IDS):
        logger.error("No GROUP_CHAT_IDS configured!")
        return
    
    while True:
        try:
            await send_signal()
            await asyncio.sleep(random.randint(280, 320))  # 5 min ± variation
            
            await send_register()
            await asyncio.sleep(random.randint(880, 920))  # 15 min ± variation
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(60)  # Wait before retrying

# Flask Routes
@app.route('/')
def health_check():
    return jsonify({"status": "ok", "message": "Telegram bot is running"})

@app.route('/send-signal')
async def send_signal_endpoint():
    try:
        await send_signal()
        return jsonify({"status": "success", "message": "Signal sent to all channels"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/send-register')
async def send_register_endpoint():
    try:
        await send_register()
        return jsonify({"status": "success", "message": "Register message sent to all channels"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def run_bot():
    """Function to run the bot in a separate thread"""
    asyncio.run(main())

if __name__ == "__main__":
    # Start the bot in a separate thread
    import threading
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start the Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
