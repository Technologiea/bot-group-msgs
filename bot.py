import asyncio
import random
import logging
import os
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from telegram import Bot
from telegram.error import TelegramError

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_IDS = os.getenv('GROUP_CHAT_IDS', '').split(',')
REGISTER_LINK = os.getenv('REGISTER_LINK', 'https://lkpf.pro/98c42daa')
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Kolkata')
CURRENCY_SYMBOL = os.getenv('CURRENCY_SYMBOL', '₹')
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
    weighted_emojis = []
    for emoji, weight in REACTION_WEIGHTS.items():
        weighted_emojis.extend([emoji] * weight)
    return " ".join(random.sample(weighted_emojis, 5))

def get_bet_time():
    now = datetime.now(ZoneInfo(TIMEZONE))
    bet_time = now + timedelta(minutes=random.randint(3, 8))
    return bet_time.strftime("%I:%M %p")

def is_signal_time():
    """Check if current time is between 8 PM and 12:35 AM"""
    now = datetime.now(ZoneInfo(TIMEZONE))
    current_time = now.time()
    return time(20, 0) <= current_time or current_time <= time(0, 35)

def is_last_signal_time():
    """Check if current time is between 12:30 AM and 12:35 AM"""
    now = datetime.now(ZoneInfo(TIMEZONE))
    current_time = now.time()
    return time(0, 30) <= current_time <= time(0, 35)

def is_registration_reminder_time():
    """Check if current time is within 5 minutes of 10 AM, 1 PM, or 4 PM"""
    now = datetime.now(ZoneInfo(TIMEZONE))
    current_time = now.time()
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
            await asyncio.sleep(1)  # Avoid rate limiting
        except TelegramError as e:
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

async def send_register_to_chat(chat_id):
    """Send register message to a specific chat"""
    message = random.choice(DAYTIME_REGISTER_TEMPLATES).format(
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
    
    while True:
        try:
            now = datetime.now(ZoneInfo(TIMEZONE))
            
            # Signal time: 8 PM to 12:35 AM
            if is_signal_time():
                # Send signal every 15 minutes
                if last_signal_time is None or (now - last_signal_time).total_seconds() >= 900:
                    await send_to_all_channels(send_signal_to_chat)
                    last_signal_time = now
                    # If last signal, wait until after 12:35 AM
                    if is_last_signal_time():
                        await asyncio.sleep(300)  # Wait 5 minutes
                    else:
                        await asyncio.sleep(60)  # Check every minute
                else:
                    await asyncio.sleep(60)  # Check every minute
            
            # Registration reminder time: 10 AM, 1 PM, 4 PM
            elif is_registration_reminder_time():
                # Send registration message once per time slot
                if last_registration_time is None or (now - last_registration_time).total_seconds() >= 3600:
                    await send_to_all_channels(send_register_to_chat)
                    last_registration_time = now
                    await asyncio.sleep(300)  # Wait 5 minutes to avoid duplicates
                else:
                    await asyncio.sleep(60)  # Check every minute
            
            else:
                # Calculate sleep time until next active period
                current_time = now.time()
                next_time = None
                if current_time < time(10, 0):
                    next_time = datetime.combine(now.date(), time(10, 0), tzinfo=ZoneInfo(TIMEZONE))
                elif current_time < time(13, 0):
                    next_time = datetime.combine(now.date(), time(13, 0), tzinfo=ZoneInfo(TIMEZONE))
                elif current_time < time(16, 0):
                    next_time = datetime.combine(now.date(), time(16, 0), tzinfo=ZoneInfo(TIMEZONE))
                elif current_time < time(20, 0):
                    next_time = datetime.combine(now.date(), time(20, 0), tzinfo=ZoneInfo(TIMEZONE))
                else:
                    # After 12:35 AM, wait until 10 AM next day
                    next_time = datetime.combine(now.date() + timedelta(days=1), time(10, 0), tzinfo=ZoneInfo(TIMEZONE))
                
                sleep_seconds = (next_time - now).total_seconds()
                if sleep_seconds > 0:
                    logger.info(f"Sleeping until {next_time.strftime('%I:%M %p')} ({sleep_seconds} seconds)")
                    await asyncio.sleep(sleep_seconds)
                else:
                    await asyncio.sleep(60)  # Fallback
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute

if __name__ == "__main__":
    asyncio.run(main())
