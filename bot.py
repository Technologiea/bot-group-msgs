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
REGISTER_LINK = os.getenv('REGISTER_LINK', 'https://1win.com')
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Kolkata')
CURRENCY_SYMBOL = os.getenv('CURRENCY_SYMBOL', '$')
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

# Signal message templates for specific times
SIGNAL_TEMPLATES = [
    """🏆 *PROVEN WIN SIGNAL* 🏆

🔥 *Last signal hit 5x! Get 500% BONUS now!*

⏰ Bet Time: {bet_time}
🎯 Cash Out Target: {multiplier}x

🌟 *Be the next winner!*

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

⚡ *Join 1Win Lucky Jet - Your Path to Daily $1000+*

💬 *DM @DOREN99 for support and help.*
{reactions}""",

    """🚀 *ELITE WINNING SIGNAL* 🚀

💎 *Special Bonus:* **500% EXTRA** on first deposit!

🕒 Bet Time: {bet_time}
📈 Target Multiplier: {multiplier}x

💰 *Daily $1000+ Earnings Possible!*

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

🌟 *1Win Partner - Trusted by Thousands*

💬 *DM @DOREN99 for support and help.*
{reactions}""",

    """⭐ *PREMIUM 1WIN SIGNAL* ⭐

🎯 *Proven Strategy for Consistent Wins!*

⏰ Bet Time: {bet_time}
🎯 Cash Out Target: {multiplier}x

💵 *Earn $1000+ Daily with Our Signals*

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

🔥 *Join the Winning Team Today!*

💬 *DM @DOREN99 for support and help.*
{reactions}"""
]

# Success message template after each signal
SUCCESS_TEMPLATE = """🎉 *SIGNAL PASSED SUCCESSFULLY!* 🎉

💰 *EARNED PROFIT: {currency_symbol}{profit:,}!*
🔥 *IT'S YOUR TIME TO EARN NOW!*

💵 *Daily Target: $1000+ Achievable!*
🚀 *Next Signal Coming Soon!*

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

🌟 *1Win Lucky Jet - Your Gateway to Financial Freedom*

💬 *DM @DOREN99 for support and help.*
{reactions}"""

# Morning registration message for 10:35 AM
MORNING_SIGNAL_TEMPLATE = """🏆 *PROVEN WIN SIGNAL* 🏆

🔥 *Last signal hit 5x! Get 500% BONUS now!*

⏰ Bet Time: 11:00 AM
🎯 Cash Out Target: {multiplier}x

🌟 *Be the next winner!*

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

💵 *Start Your Journey to Daily $2000 Earnings!*

💬 *DM @DOREN99 for support and help.*
{reactions}"""

# Daily earnings motivation template
EARNINGS_TEMPLATE = """💸 *DAILY EARNINGS UPDATE* 💸

📊 *Today's Total: {currency_symbol}{daily_total:,}*
🎯 *Next Target: {currency_symbol}{next_target:,}*

🔥 *Consistent $1000+ Daily Earnings!*
🚀 *Join Our Winning Team Now!*

✨ *Why Choose 1Win Lucky Jet?*
✅ **Proven Signals**
✅ **Instant Withdrawals** 
✅ **24/7 Support**
✅ **500% Welcome Bonus**

🔗 [REGISTER NOW]({register_link}) 
👉 [DEPOSIT NOW]({register_link})

💬 *DM @DOREN99 for support and help.*
{reactions}"""

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
    return random.randint(500, 2000)  # Profits in dollars $500-$2000

def random_daily_total():
    return random.randint(1000, 3000)  # Daily totals $1000-$3000

def random_reactions():
    weighted_emojis = []
    for emoji, weight in REACTION_WEIGHTS.items():
        weighted_emojis.extend([emoji] * weight)
    return " ".join(random.sample(weighted_emojis, 5))

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
    message = random.choice(SIGNAL_TEMPLATES).format(
        bet_time=bet_time,
        multiplier=multiplier,
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

async def send_morning_signal_to_chat(chat_id, multiplier):
    """Send morning signal to a specific chat"""
    message = MORNING_SIGNAL_TEMPLATE.format(
        multiplier=multiplier,
        register_link=REGISTER_LINK,
        reactions=random_reactions()
    )
    
    await bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
    logger.info(f"Morning signal sent to {chat_id}")

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

async def send_earnings_to_chat(chat_id):
    """Send daily earnings motivation message"""
    message = EARNINGS_TEMPLATE.format(
        currency_symbol=CURRENCY_SYMBOL,
        daily_total=random_daily_total(),
        next_target=random.randint(1000, 2000),
        register_link=REGISTER_LINK,
        reactions=random_reactions()
    )
    
    await bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
    logger.info(f"Earnings motivation sent to {chat_id}")

async def main():
    logger.info("1Win Lucky Jet Bot started successfully...")
    print("Bot is running. Press Ctrl+C to stop.")
    
    signal_times = [
        (10, 35),  # 10:35 AM - Morning signal announcement
        (11, 0),   # 11:00 AM - First signal
        (11, 5),   # 11:05 AM - Success message
        (14, 0),   # 2:00 PM - Second signal
        (14, 5),   # 2:05 PM - Success message
        (15, 0),   # 3:00 PM - Third signal
        (15, 5),   # 3:05 PM - Success message
        (19, 0),   # 7:00 PM - Fourth signal
        (19, 5),   # 7:05 PM - Success message
        (21, 0),   # 9:00 PM - Fifth signal
        (21, 5),   # 9:05 PM - Success message
        (0, 0),    # 12:00 AM - Sixth signal
        (0, 5)     # 12:05 AM - Success message
    ]
    
    last_signal_time = None
    daily_earnings_sent = False
    
    while True:
        try:
            now = datetime.now(ZoneInfo(TIMEZONE))
            current_time = now.time()
            
            # Reset daily earnings flag at 10 AM
            if current_time.hour == 10 and current_time.minute == 0:
                daily_earnings_sent = False
            
            # Check if it's time for any scheduled signal
            for hour, minute in signal_times:
                if (current_time.hour == hour and 
                    current_time.minute == minute and 
                    (last_signal_time is None or 
                     (now - last_signal_time).total_seconds() >= 300)):  # 5 minutes minimum gap
                    
                    if (hour, minute) == (10, 35):
                        # Morning signal announcement
                        logger.info("Sending morning signal announcement")
                        multiplier = random_multiplier()
                        await send_to_all_channels(lambda chat_id: send_morning_signal_to_chat(chat_id, multiplier))
                    
                    elif minute == 0:  # Signal time (XX:00)
                        logger.info(f"Sending signal for {hour:02d}:{minute:02d}")
                        multiplier = random_multiplier()
                        bet_time = f"{hour:02d}:{minute:02d} {'AM' if hour < 12 else 'PM'}"
                        await send_to_all_channels(lambda chat_id: send_signal_to_chat(chat_id, bet_time, multiplier))
                    
                    elif minute == 5:  # Success message (XX:05)
                        logger.info(f"Sending success message for {hour:02d}:{minute:02d}")
                        await send_to_all_channels(send_success_to_chat)
                        
                        # Send daily earnings motivation after 2 PM success
                        if hour == 14 and not daily_earnings_sent:
                            await asyncio.sleep(2)
                            logger.info("Sending daily earnings motivation")
                            await send_to_all_channels(send_earnings_to_chat)
                            daily_earnings_sent = True
                    
                    last_signal_time = now
                    await asyncio.sleep(60)  # Wait 1 minute before next check
                    break
            else:
                # No signal time matched, sleep until next minute
                next_minute = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
                sleep_seconds = (next_minute - now).total_seconds()
                if sleep_seconds > 0:
                    await asyncio.sleep(sleep_seconds)
                else:
                    await asyncio.sleep(30)  # Fallback
                    
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute

# Flask endpoint for Render health check
@app.route('/health')
def health_check():
    return jsonify({"status": "ok", "message": "1Win Lucky Jet bot is running"})

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
