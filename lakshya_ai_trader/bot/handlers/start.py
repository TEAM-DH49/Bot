"""
Start and Help Command Handlers
Handle /start and /help commands
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select

from database.models import User
from database.connection import db_manager
from config.constants import MESSAGES_EN, MESSAGES_HI

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        
        # Create or update user in database
        async with db_manager.session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                # Update existing user
                user.username = username
                user.first_name = first_name
                user.last_name = last_name
                from datetime import datetime
                user.last_active = datetime.utcnow()
            else:
                # Create new user
                user = User(
                    id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                session.add(user)
            
            await session.commit()
        
        # Welcome message
        welcome_msg = f"""
🎯 <b>Welcome to Lakshya AI Trader!</b>

Namaste {first_name}! 👋

I'm your personal Indian stock market analysis bot powered by advanced AI and real-time data.

<b>🚀 What I Can Do:</b>
• Live stock quotes (NSE/BSE)
• Technical analysis (RSI, MACD, Bollinger Bands)
• AI-powered insights
• Price alerts
• Watchlist management
• Portfolio tracking
• News & sentiment analysis
• Auto scanner for opportunities
• Market indices tracking

<b>🎓 Quick Start:</b>
Try these commands:
• /quote RELIANCE - Get live price
• /ta TCS - Technical analysis
• /ai INFY - AI insights
• /help - See all commands

<b>💡 Tip:</b> You can also just send stock symbols like "RELIANCE" or "TCS" and I'll fetch the data!

⚠️ <i>Educational purpose only. Not financial advice.</i>

Ready to explore the market? Let's go! 🚀
"""
        
        # Inline keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📚 Help", callback_data="help"),
                InlineKeyboardButton(text="📊 Indices", callback_data="indices")
            ],
            [
                InlineKeyboardButton(text="🔍 Scanner", callback_data="scanner"),
                InlineKeyboardButton(text="📝 Watchlist", callback_data="watchlist")
            ]
        ])
        
        await message.answer(welcome_msg, reply_markup=keyboard)
        
        logger.info(f"User {user_id} ({username}) started the bot")
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await message.answer("Sorry, something went wrong. Please try again.")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    try:
        help_msg = """
📚 <b>Lakshya AI Trader - Commands Guide</b>

<b>📈 Stock Data Commands:</b>
/quote SYMBOL - Live stock quote
   Example: /quote RELIANCE

/ta SYMBOL - Technical analysis
   Example: /ta TCS

/ai SYMBOL - AI-powered insights
   Example: /ai INFY

/news SYMBOL - Latest news
   Example: /news HDFC

<b>🔔 Alert Commands:</b>
/alert add SYMBOL above PRICE
   Example: /alert add RELIANCE above 2900

/alert add SYMBOL below PRICE
   Example: /alert add TCS below 3800

/alert list - Show all alerts
/alert delete ID - Delete alert

<b>📝 Watchlist Commands:</b>
/watchlist - Show your watchlist
/watchlist add SYMBOL - Add stock
/watchlist remove SYMBOL - Remove stock

<b>💼 Portfolio Commands:</b>
/portfolio - Show your holdings
/portfolio add SYMBOL QTY PRICE
   Example: /portfolio add INFY 10 1500

/portfolio remove SYMBOL - Remove holding

<b>🔍 Scanner & Analysis:</b>
/scanner - Auto-detect opportunities
/scanner oversold - Find oversold stocks
/scanner breakout - Find breakouts
/indices - Market indices dashboard
/sectors - Sector performance

<b>📊 Advanced Features:</b>
/compare SYMBOL1 SYMBOL2 SYMBOL3
   Example: /compare TCS INFY WIPRO

/timeframe SYMBOL - Multi-timeframe analysis
/patterns SYMBOL - Chart pattern detection
/backtest STRATEGY SYMBOL PERIOD

<b>⚙️ Settings:</b>
/digest on/off - Toggle daily digest
/language hindi/english - Change language
/settings - View your settings

<b>💡 Pro Tips:</b>
• Just send symbol name: "RELIANCE" or "TCS"
• Use commas for multiple: "RELIANCE, TCS, INFY"
• Ask questions naturally: "Reliance abhi buy karna sahi hai?"

<b>🆘 Support:</b>
/feedback - Send feedback
/about - About this bot

⚠️ <i>All information is for educational purposes only.</i>
<i>Not financial advice. Trade at your own risk.</i>
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Home", callback_data="start")]
        ])
        
        await message.answer(help_msg, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await message.answer("Sorry, something went wrong.")


@router.message(Command("about"))
async def cmd_about(message: Message):
    """Handle /about command"""
    about_msg = """
<b>🎯 Lakshya AI Trader</b>

<b>Version:</b> 1.0.0
<b>Developer:</b> @LakshyaAI
<b>Purpose:</b> Educational Indian Stock Market Analysis

<b>🌟 Features:</b>
✅ Real-time NSE/BSE stock data
✅ Advanced technical analysis
✅ AI-powered insights (Gemini)
✅ News sentiment analysis
✅ Portfolio & watchlist tracking
✅ Smart alert system
✅ Auto scanner for opportunities

<b>📊 Data Sources:</b>
• Yahoo Finance (Primary)
• Alpha Vantage (Backup)
• Finnhub (News)
• OpenRouter AI (Analysis)

<b>🔒 Privacy:</b>
We don't store any sensitive financial data.
Only usernames and preferences are saved.

<b>⚠️ Disclaimer:</b>
This bot provides educational information only.
Not financial advice. Always do your own research.
Trading involves risk. Invest wisely.

<b>💬 Feedback & Support:</b>
Found a bug? Have suggestions?
Use /feedback to reach us!

<b>⭐ Like this bot?</b>
Share it with fellow traders!

Made with ❤️ for Indian traders
"""
    
    await message.answer(about_msg)


@router.message(Command("feedback"))
async def cmd_feedback(message: Message):
    """Handle /feedback command"""
    feedback_msg = """
💬 <b>Send Your Feedback</b>

We'd love to hear from you!

<b>How to send feedback:</b>
Reply to this message with your feedback, suggestions, or bug reports.

<b>What to include:</b>
• Feature requests
• Bug reports (with steps to reproduce)
• General suggestions
• What you like/dislike

Your feedback helps us improve! 🙏

<i>Note: Due to Telegram limitations, please send feedback via direct message or use the command:</i>
/feedback Your feedback here
"""
    
    await message.answer(feedback_msg)
