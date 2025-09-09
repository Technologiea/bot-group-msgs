import asyncio
import random
import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram import Bot
from telegram.error import TelegramError

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')
REGISTER_LINK = os.getenv('REGISTER_LINK', 'https://1wytkd.com/v3/lucky-jet-updated?p=qye5')
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

async def send_signal():
    try:
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
            chat_id=GROUP_CHAT_ID,
            text=message,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        logger.info(f"Signal sent for Bet Time {bet_time}")
        
    except TelegramError as e:
        logger.error(f"Error sending signal: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

async def send_register():
    try:
        message = random.choice(REGISTER_TEMPLATES).format(
            currency_symbol=CURRENCY_SYMBOL,
            register_link=REGISTER_LINK,
            reactions=random_reactions()
        )
        
        await bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=message,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        logger.info("Register message sent.")
        
    except TelegramError as e:
        logger.error(f"Error sending register message: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

async def main():
    logger.info("Bot started successfully...")
    print("Bot is running. Press Ctrl+C to stop.")
    
    while True:
        try:
            await send_signal()
            await asyncio.sleep(random.randint(280, 320))  # 5 min ± variation
            
            await send_register()
            await asyncio.sleep(random.randint(880, 920))  # 15 min ± variation
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
