import asyncio
import random
import logging
import os
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from telegram import Bot
from telegram.error import TelegramError
from flask import Flask, jsonify
import threading

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_IDS = os.getenv('GROUP_CHAT_IDS', '').split(',')
REGISTER_LINK = os.getenv('REGISTER_LINK', 'https://lkpq.cc/eec3')
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Kolkata')
CURRENCY_SYMBOL = os.getenv('CURRENCY_SYMBOL', '₹')
PORT = int(os.getenv('PORT', 5000))
# --- CONFIGURATION ---

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Validate environment variables
if not BOT_TOKEN:
    logger.error("BOT_TOKEN is not set!")
    exit(1)
if not GROUP_CHAT_IDS or not any(GROUP_CHAT_IDS):
    logger.error("No GROUP_CHAT_IDS configured!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# Signal message templates for 8 PM to 12:30 AM (2 signals per hour)
SIGNAL_TEMPLATES = [
    """🚀 *LUCKYJET SIGNAL ALERT* 🚀

🔥 *Limited Offer:* Get **500% BONUS** on your first deposit!

⏰ Bet Time: {bet_time}
🎯 Cash Out Target: {multiplier}x

✨ *Your winning moment is now!*

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

⚡ Turn **{currency_symbol}10** into **{currency_symbol}60+**!

💬 *DM @DOREN99 for support and help.*
{reactions}""",

    """🎰 *WINNING SIGNAL CONFIRMED* 🎰

💎 *Special Bonus:* **500% EXTRA** on first deposit!

🕒 Recommended Time: {bet_time}
📈 Target Multiplier: {multiplier}x

🌟 *Join thousands winning big!*

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

🚀 **{currency_symbol}20** can become **{currency_symbol}100+**!

💬 *DM @DOREN99 for support and help.*
{reactions}""",

    """🏆 *PROVEN WIN SIGNAL* 🏆

🔥 *Last signal hit 5x!* Get **500% BONUS** now!

⏰ Bet Time: {bet_time}
🎯 Cash Out Target: {multiplier}x

🌟 *Be the next winner!*

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

⚡ Start with **{currency_symbol}10** and win big!

💬 *DM @DOREN99 for support and help.*
{reactions}"""
]

# Last signal of the day template
LAST_SIGNAL_TEMPLATE = """⚠️ *LAST SIGNAL OF THE DAY* ⚠️
🚀 *FINAL CHANCE TO WIN TODAY* 🚀

🔥 *Don't miss out!* Get **500% BONUS** now!

⏰ Bet Time: {bet_time}
🎯 Cash Out Target: {multiplier}x

✨ *This is your final shot today!*

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

⚡ **{currency_symbol}10** can multiply fast!

💬 *DM @DOREN99 for support and help.*
{reactions}"""

# Success message template after each signal
SUCCESS_TEMPLATE = """🎉 *SIGNAL PASSED SUCCESSFULLY!* 🎉

💰 *EARNED PROFIT: {currency_symbol}{profit:,}!*
🔥 *IT'S YOUR TIME TO EARN NOW!*

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

💬 *DM @DOREN99 for support and help.*
{reactions}"""

# Goodnight message template after last signal
GOODNIGHT_TEMPLATE = """🌙 *GOODNIGHT, WINNERS!* 🌙

🎉 *Today's signals rocked!* Ready for more tomorrow?

🔥 *Sign up now for 500% BONUS* and join our winning team!

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

⏰ *Next signals start at 8 PM tomorrow!*

💬 *DM @DOREN99 for support and help.*
{reactions}"""

# Registration message templates for 9 AM, 1 PM, 4 PM, and 7 PM
DAYTIME_REGISTER_TEMPLATES = [
    """🌅 *MORNING WIN ALERT* 🌅

Kickstart your day with a **500% BONUS**! Thousands are winning with our signals.

✨ *Why join?*
✅ **1-minute signup** via UPI
✅ **High win-rate signals**
✅ **Instant withdrawals**

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

📈 *Tip:* Bet at signal time, cash out at target!
⚡ Free signals at **8 PM tonight**!

💬 *DM @DOREN99 for support and help.*
{reactions}""",

    """☀️ *AFTERNOON HURRY* ☀️

Don't miss tonight's signals! **500% BONUS** on your first deposit!

🎯 *Tonight's Plan:*
⏰ **8 PM - 12:30 AM**: 2 signals per hour

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

📈 *Tip:* Bet at signal time, cash out at target!
⚡ Join now for **8 PM signals**!

💬 *DM @DOREN99 for support and help.*
{reactions}""",

    """🌇 *EVENING RUSH* 🌇

Last chance to join before **8 PM signals**! Get **500% BONUS** now!

✨ *Why us?*
✅ **Proven signals**
✅ **Secure deposits**
✅ **Fast payouts**

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

📈 *Tip:* Bet at signal time, cash out at target!
⚡ **8 PM signals await**!

💬 *DM @DOREN99 for support and help.*
{reactions}""",

    """🔥 *HYPE ALERT: SIGNALS SOON* 🔥

**1 hour until 8 PM signals**! Sign up for **500% BONUS** now!

🎯 *Tonight's schedule:*
✅ **8 PM - 12:30 AM**: 2 signals per hour
✅ **High multipliers**
✅ **Real-time alerts**

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

📈 *Tip:* Bet at signal time, cash out at target!
⚡ **Get ready for 8 PM**!

💬 *DM @DOREN99 for support and help.*
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
    "✨": 2,  # 2 times more likely
    "🏆": 3,  # Winning theme
    "📈": 3   # Winning theme
}

def random_multiplier():
    return round(random.uniform(1.5, 12.5), 2)

def random_profit():
    return random.randint(10000, 50000) // 1000 * 1000  # Profits in thousands (₹10,000-₹50,000)

def random_reactions():
    weighted_emojis = []
    for emoji, weight in REACTION_WEIGHTS.items():
        weighted_emojis.extend([emoji] * weight)
    return " ".join(random.sample(weighted_emojis, 5))

def get_bet_time():
    now = datetime.now(ZoneInfo(TIMEZONE))
    bet_time = now + timedelta(minutes=random.randint(3, 8))
    return bet_time

async def send_to_all_channels(message_func):
    """Helper function to send messages to all channels"""
    for chat_id in GROUP_CHAT_IDS:
        if not chat_id.strip():
            continue
        try:
            await message_func(chat_id.strip())
            await asyncio.sleep(1)  # Avoid rate limiting
        except TelegramError as e:
            logger.error(f"Error sending to {chat_id}: {e}")

async def send_signal_to_chat(chat_id, bet_time, multiplier):
    """Send signal to a specific chat"""
    if is_last_signal_time():
        message = LAST_SIGNAL_TEMPLATE.format(
            bet_time=bet_time.strftime("%I:%M %p"),
            multiplier=multiplier,
            currency_symbol=CURRENCY_SYMBOL,
            register_link=REGISTER_LINK,
            reactions=random_reactions()
        )
    else:
        message = random.choice(SIGNAL_TEMPLATES).format(
            bet_time=bet_time.strftime("%I:%M %p"),
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
    logger.info(f"Signal sent to {chat_id} for Bet Time {bet_time.strftime('%I:%M %p')}")

async def send_success_to_chat(chat_id):
    """Send success message to a specific chat"""
    message = SUCCESS_TEMPLATE.format(
        currency_symbol=CURRENCY_SYMBOL,
        profit=random_profit(),
        register_link=REGISTER_LINK,
        reactions=random_reactions()
    )
    
    await bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
    logger.info(f"Success message sent to {chat_id}")

async def send_goodnight_to_chat(chat_id):
    """Send goodnight message to a specific chat"""
    message = GOODNIGHT_TEMPLATE.format(
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
    logger.info(f"Goodnight message sent to {chat_id}")

async def send_register_to_chat(chat_id):
    """Send register message to a specific chat"""
    now = datetime.now(ZoneInfo(TIMEZONE))
    current_time = now.time()
    # Select template based on time (7 PM uses the last template)
    if time(19, 0) <= current_time <= time(19, 5):
        message = DAYTIME_REGISTER_TEMPLATES[3].format(
            currency_symbol=CURRENCY_SYMBOL,
            register_link=REGISTER_LINK,
            reactions=random_reactions()
        )
    else:
        message = random.choice(DAYTIME_REGISTER_TEMPLATES[:3]).format(
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

async def main():
    logger.info("Bot started successfully...")
    print("Bot is running. Press Ctrl+C to stop.")
    
    last_signal_time = None
    last_registration_time = None
    goodnight_sent = False
    signal_queue = []  # List to store (bet_time, multiplier) tuples
    
    while True:
        try:
            now = datetime.now(ZoneInfo(TIMEZONE))
            
            # Reset goodnight flag daily
            if now.time() < time(0, 30):
                goodnight_sent = False
            
            # Process success messages for signals whose bet time has passed
            expired_signals = [(bet_time, multiplier) for bet_time, multiplier in signal_queue 
                              if now >= bet_time + timedelta(minutes=1)]
            for bet_time, multiplier in expired_signals:
                logger.info(f"Sending success message for signal with Bet Time {bet_time.strftime('%I:%M %p')}")
                await send_to_all_channels(send_success_to_chat)
                signal_queue.remove((bet_time, multiplier))
            
            # Signal time: 8 PM to 12:30 AM (2 signals per hour)
            if is_signal_time():
                # Send signals at :00 and :30 of each hour
                current_minute = now.minute
                
                # Check if it's time for a signal (:00 or :30 minute)
                if current_minute in [0, 30] and (last_signal_time is None or 
                    (now - last_signal_time).total_seconds() >= 1200):  # 20 minutes minimum gap
                    
                    bet_time = get_bet_time()
                    multiplier = random_multiplier()
                    logger.info(f"Sending signal at {now.strftime('%H:%M')}")
                    await send_to_all_channels(lambda chat_id: send_signal_to_chat(chat_id, bet_time, multiplier))
                    signal_queue.append((bet_time, multiplier))
                    last_signal_time = now
                    
                    # If last signal, send goodnight message and wait
                    if is_last_signal_time() and not goodnight_sent:
                        await asyncio.sleep(30)  # Short delay before goodnight
                        logger.info("Sending goodnight message")
                        await send_to_all_channels(send_goodnight_to_chat)
                        goodnight_sent = True
                        await asyncio.sleep(300)  # Wait 5 minutes
                else:
                    await asyncio.sleep(30)  # Check every 30 seconds
            
            # Registration reminder time: 9 AM, 1 PM, 4 PM, 7 PM
            elif is_registration_reminder_time():
                # Send registration message once per time slot
                if last_registration_time is None or (now - last_registration_time).total_seconds() >= 3600:
                    logger.info("Sending registration reminder")
                    await send_to_all_channels(send_register_to_chat)
                    last_registration_time = now
                    await asyncio.sleep(300)  # Wait 5 minutes to avoid duplicates
                else:
                    await asyncio.sleep(60)  # Check every minute
            
            else:
                # Calculate sleep time until next active period
                current_time = now.time()
                next_time = None
                
                if current_time < time(9, 0):
                    next_time = datetime.combine(now.date(), time(9, 0), tzinfo=ZoneInfo(TIMEZONE))
                elif current_time < time(13, 0):
                    next_time = datetime.combine(now.date(), time(13, 0), tzinfo=ZoneInfo(TIMEZONE))
                elif current_time < time(16, 0):
                    next_time = datetime.combine(now.date(), time(16, 0), tzinfo=ZoneInfo(TIMEZONE))
                elif current_time < time(19, 0):
                    next_time = datetime.combine(now.date(), time(19, 0), tzinfo=ZoneInfo(TIMEZONE))
                elif current_time < time(20, 0):
                    next_time = datetime.combine(now.date(), time(20, 0), tzinfo=ZoneInfo(TIMEZONE))
                else:
                    # After 12:30 AM, wait until 9 AM next day
                    next_time = datetime.combine(now.date() + timedelta(days=1), time(9, 0), tzinfo=ZoneInfo(TIMEZONE))
                
                sleep_seconds = (next_time - now).total_seconds()
                if sleep_seconds > 0:
                    logger.info(f"Sleeping until {next_time.strftime('%I:%M %p')} ({sleep_seconds} seconds)")
                    await asyncio.sleep(sleep_seconds)
                else:
                    await asyncio.sleep(60)  # Fallback
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute

def is_signal_time():
    """Check if current time is between 8 PM and 12:30 AM"""
    now = datetime.now(ZoneInfo(TIMEZONE))
    current_time = now.time()
    return time(20, 0) <= current_time or current_time <= time(0, 30)

def is_last_signal_time():
    """Check if current time is between 12:25 AM and 12:30 AM"""
    now = datetime.now(ZoneInfo(TIMEZONE))
    current_time = now.time()
    return time(0, 25) <= current_time <= time(0, 30)

def is_registration_reminder_time():
    """Check if current time is within 5 minutes of 9 AM, 1 PM, 4 PM, or 7 PM"""
    now = datetime.now(ZoneInfo(TIMEZONE))
    current_time = now.time()
    target_times = [time(9, 0), time(13, 0), time(16, 0), time(19, 0)]
    for target in target_times:
        if (current_time.hour == target.hour and 
            current_time.minute >= target.minute and 
            current_time.minute <= target.minute + 5):
            return True
    return False

# Flask endpoint for Render health check
@app.route('/health')
def health_check():
    return jsonify({"status": "ok", "message": "Telegram bot is running"})

def run_bot():
    """Run the bot in a separate thread"""
    asyncio.run(main())

if __name__ == "__main__":
    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start Flask app for Render port binding
    app.run(host='0.0.0.0', port=PORT)
