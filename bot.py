import asyncio
import random
import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import TelegramError
from flask import Flask, jsonify
import threading

# ========================= CONFIG =========================
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_IDS = [int(x.strip()) for x in os.getenv('GROUP_CHAT_IDS', '').split(',') if x.strip()]
REGISTER_LINK = "https://lkpq.cc/2ee301"
PROMOCODE = "BETWIN190"
TIMEZONE_IST = "Asia/Kolkata"
CURRENCY_SYMBOL = "$"
PORT = int(os.getenv('PORT', 5000))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

if not BOT_TOKEN or not GROUP_CHAT_IDS:
    logger.error("BOT_TOKEN or GROUP_CHAT_IDS missing!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# ========================= KEYBOARD =========================
def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 DEPOSIT $100 → GET $600 (500% BONUS)", url=REGISTER_LINK)],
        [InlineKeyboardButton("🔥 ACTIVATE BETWIN190 BONUS NOW", url=REGISTER_LINK)],
        [InlineKeyboardButton("✅ REGISTER & PLAY — INSTANT WITHDRAWAL", url=REGISTER_LINK)]
    ])

# ========================= MESSAGES (15 PREMIUM TEMPLATES) =========================
ALERT_MSGS = [
    """🚨 **VOLATILITY 100 JUST EXPLODED** 🚨\n\nLucky Jet is in **GOD MODE** right now!\n\n👥 Players Online: **{online}+**\n💸 Deposits (last 9 min): **{deposits}+**\n\nNext cashout: **~{preview}x** in <5 mins\n\nOnly **39 VIP seats** left before lock!\n\n[GET +500% BONUS → BETWIN190]({link})""",
    
    """⚡ **MASSIVE SIGNAL DETECTED** ⚡\n\nLucky Jet entering **HYPER MODE**\nAll regions going crazy!\n\n📈 {online}+ players active\n💰 {deposits}+ deposits in 9 mins\n\nPredicted: **{preview}x** hitting soon\n\nDon’t miss the biggest one tonight!\n\n[CLAIM 500% BONUS NOW]({link})""",
    
    """🎯 **GOD-TIER SIGNAL LOADING** 🎯\n\nLucky Jet about to **PRINT MONEY**\n\n🔥 {online}+ warriors online\n💎 {deposits}+ deposits rushing in\n\nNext multiplier: **{preview}x+**\n\nLast chance before auto-lock!\n\n[SECURE YOUR 500% BONUS]({link})"""
]

LIVE_MSGS = [
    """✅ **LIVE SIGNAL — ENTER NOW** ✅\n\n🎮 Game: **Lucky Jet**\n🕐 Time: **{time}** IST\n\n💥 CASH OUT AT: **{multiplier}×** (LOCKED)\n\n✅ Accuracy: **99.4%** (11/12 wins)\n\n💰 $100 → ${profit}\n💰 $50 → ${half_profit}\n\n⏰ You have 22 seconds!\n\n[INSTANT DEPOSIT → BETWIN190]({link})""",
    
    """🚀 **LIVE — JUMP IN RIGHT NOW** 🚀\n\nLucky Jet **LIVE SIGNAL**\n\n🎯 Target: **{multiplier}×**\n🕐 {time} IST\n\nLast 5 hits: 7.8x · 9.1x · 12.6x · 18.3x → **24.7x**\n\n$100 becomes **${profit}** in seconds!\n\n[TAP TO DEPOSIT & WIN]({link})""",
    
    """🔴 **LIVE BET — DON’T MISS** 🔴\n\nLucky Jet **GOING PARABOLIC**\n\n💥 Multiplier: **{multiplier}×**\n⏰ {time} IST\n\n$100 → **${profit}** instant profit\n\n97 legends already in!\n\n[DEPOSIT $100 GET $600 NOW]({link})"""
]

SUCCESS_MSGS = [
    """🎉 **SIGNAL SMASHED: +{multiplier}x JUST HIT!** 🎉\n\n💰 Group profit this round: **{currency}{total:,}+**\n\n🏆 Top winner: $100 → ${win}\n🌟 Average win: **${avg}+**\n\n97 members just got PAID!\n\nType **“PAID”** if you ate tonight 😈\n\nNext monster loading in ~40 mins…""",
    
    """💥 **+{multiplier}x CONFIRMED HIT!** 💥\n\nTotal profits: **{currency}{total:,}+** in minutes\n\n🔥 $100 → ${win} (reported)\n\n87 members cashed out BIG\n\nWho else got paid? Drop **“PAID”** below!\n\nNext 20x+ coming soon…""",
    
    """🤑 **ANOTHER ONE: +{multiplier}x LANDED!** 🤑\n\nGroup made **{currency}{total:,}+** tonight\n\nBest play: $100 → ${win}\n\n94% win rate continues!\n\nNext signal in 40 mins… stay ready legends!"""
]

GUIDE_MSGS = [
    """📖 **HOW TO COLLECT EVERY SIGNAL (25sec)**\n\n1️⃣ Tap button → {link}\n2️⃣ Register (20 sec)\n3️⃣ Enter **BETWIN190**\n4️⃣ Deposit $100 → Get **$600** instantly\n5️⃣ Open Lucky Jet → Follow signals → Profit\n\n✅ Instant withdrawal\n✅ 100% trusted\n\n[CLAIM BONUS BEFORE NEXT SIGNAL]({link})""",
    
    """⚙️ **SETUP GUIDE — NEVER MISS A SIGNAL**\n\n• Click below → {link}\n• Sign up fast\n• Use code: **BETWIN190**\n• Deposit $100 = $600 total\n• Play Lucky Jet → Auto-win\n\nBonus expires soon!\n\n[GET $600 BALANCE NOW]({link})""",
    
    """🎁 **500% BONUS = YOUR UNFAIR ADVANTAGE**\n\nHow to activate in 30 seconds:\n\n👇 Tap → {link}\n👤 Register\n🎟️ Promo: **BETWIN190**\n💳 Deposit $100 → $600 credited\n\nNext signal in ~40 mins\n\n[ACTIVATE BONUS INSTANTLY]({link})"""
]

# ========================= SCHEDULER (10PM - 1AM IST, 3 msgs/hour) =========================
async def send_night_cycle():
    ist = ZoneInfo(TIMEZONE_IST)
    while True:
        now = datetime.now(ist)
        if 22 <= now.hour < 25 or (now.hour == 1 and now.minute < 20):  # 10PM to 1AM
            if now.minute % 20 == 0 and now.second < 10:  # Every 20 mins
                logger.info(f"[{now.strftime('%I:%M %p')}] Sending nightly message pack...")
                
                # Random data
                online = random.randint(420, 680)
                deposits = random.randint(78, 156)
                preview_x = round(random.uniform(13.5, 29.0), 1)
                multiplier = round(random.uniform(11.5, 31.0), 1)
                profit = int(100 * multiplier)
                half_profit = int(50 * multiplier)
                total_profit = random.randint(15200, 38900)
                avg_win = random.randint(580, 1280)
                
                time_str = now.strftime("%I:%M %p")

                # Send 4 messages with delays
                await broadcast(random.choice(ALERT_MSGS).format(
                    online=f"{online:,}", deposits=deposits, preview=preview_x, link=REGISTER_LINK
                ))
                await asyncio.sleep(210)  # 3.5 min

                await broadcast(random.choice(LIVE_MSGS).format(
                    time=time_str, multiplier=multiplier, profit=f"{profit:,}",
                    half_profit=f"{half_profit:,}", link=REGISTER_LINK
                ))
                await asyncio.sleep(180)  # 3 min

                await broadcast(random.choice(SUCCESS_MSGS).format(
                    multiplier=multiplier, total=total_profit, currency=CURRENCY_SYMBOL,
                    win=f"{profit:,}", avg=avg_win
                ))
                await asyncio.sleep(120)  # 2 min

                await broadcast(random.choice(GUIDE_MSGS).format(link=REGISTER_LINK))
                
                logger.info("Night cycle completed. Next at +20 min")
        
        await asyncio.sleep(10)

# ========================= BROADCAST =========================
async def broadcast(text: str):
    sent = 0
    for chat_id in GROUP_CHAT_IDS:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="Markdown",
                disable_web_page_preview=True,
                reply_markup=get_keyboard()
            )
            sent += 1
            await asyncio.sleep(0.8)
        except TelegramError as e:
            logger.error(f"Failed {chat_id}: {e}")
    logger.info(f"Sent to {sent}/{len(GROUP_CHAT_IDS)} groups")

# ========================= HEALTH =========================
@app.route('/health')
def health():
    return jsonify({
        "status": "LIVE - NIGHT MODE ACTIVE",
        "promocode": PROMOCODE,
        "schedule": "10:00 PM – 1:00 AM IST (3 msgs/hour)",
        "next_batch": "Every 20 minutes",
        "time_now_ist": datetime.now(ZoneInfo(TIMEZONE_IST)).strftime("%I:%M %p")
    })

# ========================= START =========================
def run_bot():
    asyncio.run(send_night_cycle())

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    logger.info("🚀 LUCKY JET BETWIN190 NIGHT BOT LIVE | 10PM - 1AM IST | 3 HIGH-CONVERSION MSGS/HOUR")
    app.run(host='0.0.0.0', port=PORT, use_reloader=False)
