import asyncio
import random
import logging
import os
from datetime import datetime, time, timedelta
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

# Signal message templates for 8 PM to 12:35 AM
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

# Last signal of the day template
LAST_SIGNAL_TEMPLATE = """⚠️ *LAST SIGNAL OF THE DAY* ⚠️
🚀 *FINAL OPPORTUNITY TO WIN TODAY* 🚀

🔥 *Don't miss out!* Get 500% BONUS on your first deposit!

⏰ Bet Time: {bet_time}
🎯 Cash Out Target: {multiplier}x

✨ *This is your final chance to win today!*

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

⚡ Start with just {currency_symbol}10 and multiply your money!
{reactions}"""

# Registration message templates for 10 AM, 1 PM, and 4 PM
DAYTIME_REGISTER_TEMPLATES = [
    """🌅 *MORNING OPPORTUNITY* 🌅

Start your day with a winning strategy! Register now and get ready for our evening signals.

🔥 *500% WELCOME BONUS* waiting for you!

✨ *Why join us?*
✅ Professional signal team
✅ High success rate
✅ Instant withdrawals
✅ 24/7 support

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

⚡ Get ready for our daily free signals starting at 8 PM!
{reactions}""",

    """☀️ *AFTERNOON REMINDER* ☀️

Don't forget to register and deposit for tonight's winning signals!

💰 *500% BONUS* on your first deposit - Limited time offer!

🎯 *Tonight's schedule:*
⏰ 8:00 PM - 12:35 AM: Free signals every 15 minutes

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

⚡ Be prepared for our evening signals!
{reactions}""",

    """🌇 *EVENING APPROACHING* 🌇

Last chance to register before our free signals start at 8 PM!

🔥 *500% BONUS* - Don't miss this opportunity!

✨ *Tonight's guaranteed signals include:*
✅ High probability wins
✅ Professional analysis
✅ Real-time updates

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

⚡ Free signals start at 8 PM sharp!
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
    
    # Select 5 unique random emojis from the weighted list
    selected_emojis = random.sample(weighted_emojis, 5)
    return " ".join(selected_emojis)

def get_bet_time():
    now = datetime.now(ZoneInfo(TIMEZONE))
    bet_time = now + timedelta(minutes=random.randint(3, 8))
    return bet_time.strftime("%I:%M %p")

def is_signal_time():
    """Check if current time is between 8 PM and 12:35 AM"""
    now = datetime.now(ZoneInfo(TIMEZONE))
    current_time = now.time()
    
    # Check if it's between 8 PM and 12:35 AM
    if time(20, 0) <= current_time or current_time <= time(0, 35):
        return True
    
    return False

def is_last_signal_time():
    """Check if current time is between 12:30 AM and 12:35 AM"""
    now = datetime.now(ZoneInfo(TIMEZONE))
    current_time = now.time()
    return time(0, 30) <= current_time <= time(0, 35)

def is_registration_reminder_time():
    """Check if current time is 10 AM, 1 PM, or 4 PM (within a 5-minute window)"""
    now = datetime.now(ZoneInfo(TIMEZONE))
    current_time = now.time()
    current_minute = now.minute
    
    # Check if it's within 5 minutes of the target times
    target_times = [time(10, 0), time(13, 0), time(16, 0)]
    for target in target_times:
        if (current_time.hour == target.hour and 
            current_time.minute >= target.minute and 
            current_time.minute <= target.minute + 5):
            return True
    
    return False

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
    
    if is_last_signal_time():
        message = LAST_SIGNAL_TEMPLATE.format(
            bet_time=bet_time,
            multiplier=multiplier,
            currency_symbol=CURRENCY_SYMBOL,
            register_link=REGISTER_LINK,
            reactions=random_reactions()
        )
    else:
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

async def send_register_to_chat(chat_id, is_daytime=True):
    """Send register message to a specific chat"""
    if is_daytime:
        message = random.choice(DAYTIME_REGISTER_TEMPLATES).format(
            currency_symbol=CURRENCY_SYMBOL,
            register_link=REGISTER_LINK,
            reactions=random_reactions()
        )
    else:
        # Use a simpler registration message during signal hours
        message = f"""🔥 *QUICK REMINDER* 🔥

Don't miss out on our signals! Register and deposit now to get started.

💰 *500% BONUS* on your first deposit!

🔗 [REGISTER NOW]({REGISTER_LINK}) 
👉 [DEPOSIT NOW]({REGISTER_LINK})

⚡ Start winning with us today!
{random_reactions()}"""
    
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

async def send_register(is_daytime=True):
    """Send register message to all channels"""
    await send_to_all_channels(lambda chat_id: send_register_to_chat(chat_id, is_daytime))

async def main():
    logger.info("Bot started successfully...")
    print("Bot is running. Press Ctrl+C to stop.")
    
    # Validate we have at least one chat ID
    if not GROUP_CHAT_IDS or not any(GROUP_CHAT_IDS):
        logger.error("No GROUP_CHAT_IDS configured!")
        return
    
    # Track last actions to prevent duplicates
    last_signal_time = None
    last_registration_time = None
    
    while True:
        try:
            now = datetime.now(ZoneInfo(TIMEZONE))
            current_time = now.time()
            
            # Check if it's signal time (8 PM to 12:35 AM)
            if is_signal_time():
                # Send signal every 15 minutes
                if last_signal_time is None or (now - last_signal_time).total_seconds() >= 900:
                    await send_signal()
                    last_signal_time = now
                    
                    # If it's the last signal time, wait longer
                    if is_last_signal_time():
                        await asyncio.sleep(300)  # Wait 5 minutes
                    else:
                        await asyncio.sleep(60)  # Wait 1 minute before next check
                else:
                    await asyncio.sleep(60)  # Wait 1 minute and check again
            
            # Check if it's registration reminder time (10 AM, 1 PM, or 4 PM)
            elif is_registration_reminder_time():
                # Send registration reminder once per time slot
                if last_registration_time is None or (now - last_registration_time).total_seconds() >= 3600:
                    await send_register(is_daytime=True)
                    last_registration_time = now
                    await asyncio.sleep(300)  # Wait 5 minutes to avoid duplicates
                else:
                    await asyncio.sleep(60)  # Wait 1 minute and check again
            
            else:
                # Not in any special time, wait 1 minute and check again
                await asyncio.sleep(60)
                
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
