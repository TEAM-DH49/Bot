"""
AI Analysis Handler
AI-powered stock analysis using OpenRouter
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from services.ai.openrouter_client import ai_client
from services.data.data_aggregator import data_aggregator
from bot.handlers.technical import get_technical_indicators
from services.news.news_fetcher import news_fetcher
from services.news.sentiment_analyzer import sentiment_analyzer
from database.redis_client import redis_client
from config.settings import settings

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("ai"))
async def cmd_ai_analysis(message: Message):
    """
    Handle /ai command for AI-powered analysis
    Usage: /ai RELIANCE
    """
    try:
        if not settings.enable_ai_analysis or not settings.openrouter_api_key:
            await message.answer(
                "❌ AI analysis is not enabled.\n\n"
                "Please configure OPENROUTER_API_KEY in settings."
            )
            return
        
        parts = message.text.split()
        
        if len(parts) < 2:
            await message.answer(
                "❌ Please provide a stock symbol\n\n"
                "Usage: /ai RELIANCE\n"
                "Example: /ai TCS"
            )
            return
        
        symbol = parts[1].upper().strip()
        
        # Check cache (AI responses are expensive)
        cache_key = f"ai:{symbol}"
        cached = await redis_client.get(cache_key)
        if cached:
            await message.answer(
                cached,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Refresh", callback_data=f"ai:{symbol}")]
                ])
            )
            return
        
        # Send status
        status_msg = await message.answer(f"🤖 AI is analyzing {symbol}... This may take a moment.")
        
        # Gather data for AI
        quote = await data_aggregator.get_stock_data(symbol)
        if "error" in quote:
            await status_msg.edit_text(f"❌ Unable to fetch data for {symbol}")
            return
        
        indicators = await get_technical_indicators(symbol)
        
        # Prepare data for AI
        analysis_data = {
            "price": quote.get("price", 0),
            "change_pct": quote.get("change_pct", 0),
            "volume": quote.get("volume", 0),
            "rsi": indicators.get("rsi", "N/A"),
            "macd_signal": indicators.get("macd", {}).get("signal_type", "N/A"),
            "volume_analysis": indicators.get("volume", {}).get("signal", "Normal")
        }
        
        # Get AI analysis
        ai_response = await ai_client.analyze_stock(symbol, analysis_data)
        
        if not ai_response:
            await status_msg.edit_text(
                "❌ AI analysis failed. Please try again later."
            )
            return
        
        # Format response
        response = f"""
🤖 <b>AI Analysis: {symbol}</b>

💰 <b>Price:</b> ₹{quote.get('price', 0):,.2f} ({quote.get('change_pct', 0):+.2f}%)

<b>📊 AI Insights:</b>
{ai_response}

<b>📈 Quick Stats:</b>
• RSI: {indicators.get('rsi', 'N/A')}
• MACD: {indicators.get('macd', {}).get('signal_type', 'N/A')}
• Volume: {indicators.get('volume', {}).get('signal', 'Normal')}

⚠️ <i>This is educational analysis, not financial advice.
AI can make mistakes. Always do your own research.</i>
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Refresh", callback_data=f"ai:{symbol}"),
                InlineKeyboardButton(text="📊 Technical", callback_data=f"ta:{symbol}")
            ],
            [
                InlineKeyboardButton(text="📰 News", callback_data=f"news:{symbol}"),
                InlineKeyboardButton(text="💰 Quote", callback_data=f"quote:{symbol}")
            ]
        ])
        
        # Cache for 5 minutes
        await redis_client.set(cache_key, response, ttl=300)
        
        await status_msg.edit_text(response, reply_markup=keyboard)
        
        logger.info(f"Sent AI analysis for {symbol} to user {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error in AI analysis command: {e}")
        await message.answer("❌ An error occurred during AI analysis.")


@router.callback_query(F.data.startswith("ai:"))
async def callback_refresh_ai(callback: CallbackQuery):
    """Handle AI analysis refresh"""
    try:
        symbol = callback.data.split(":")[1]
        
        await callback.answer("Refreshing AI analysis...")
        
        # Clear cache
        await redis_client.delete(f"ai:{symbol}")
        
        # Get fresh data
        quote = await data_aggregator.get_stock_data(symbol, force_refresh=True)
        indicators = await get_technical_indicators(symbol)
        
        analysis_data = {
            "price": quote.get("price", 0),
            "change_pct": quote.get("change_pct", 0),
            "rsi": indicators.get("rsi", "N/A"),
            "macd_signal": indicators.get("macd", {}).get("signal_type", "N/A"),
            "volume_analysis": indicators.get("volume", {}).get("signal", "Normal")
        }
        
        ai_response = await ai_client.analyze_stock(symbol, analysis_data)
        
        if not ai_response:
            await callback.message.edit_text("❌ AI analysis failed")
            return
        
        response = f"""
🤖 <b>AI Analysis: {symbol}</b>

💰 <b>Price:</b> ₹{quote.get('price', 0):,.2f} ({quote.get('change_pct', 0):+.2f}%)

<b>📊 AI Insights:</b>
{ai_response}

<b>📈 Quick Stats:</b>
• RSI: {indicators.get('rsi', 'N/A')}
• MACD: {indicators.get('macd', {}).get('signal_type', 'N/A')}

⚠️ <i>Educational analysis only. Not financial advice.</i>
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Refresh", callback_data=f"ai:{symbol}"),
                InlineKeyboardButton(text="📊 Technical", callback_data=f"ta:{symbol}")
            ]
        ])
        
        await callback.message.edit_text(response, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in AI callback: {e}")
        await callback.answer("Error refreshing AI analysis", show_alert=True)


@router.message(F.text.regexp(r'.+ (kya|hai|kaisa|kaise|kab|buy|sell|sahi|hoga|chahiye)'))
async def handle_question(message: Message):
    """
    Handle natural language questions
    Example: "Reliance abhi buy karna sahi hai?"
    """
    try:
        if not settings.enable_ai_analysis:
            return
        
        question = message.text
        
        # Check if question contains a stock symbol
        words = question.upper().split()
        from config.constants import NIFTY_50_SYMBOLS, SYMBOL_CORRECTIONS
        
        symbol = None
        for word in words:
            cleaned = word.strip("?,.")
            if cleaned in NIFTY_50_SYMBOLS:
                symbol = cleaned
                break
            if cleaned in SYMBOL_CORRECTIONS:
                symbol = SYMBOL_CORRECTIONS[cleaned]
                break
        
        await message.answer("🤖 Let me think about this...")
        
        # Prepare context if symbol found
        context = ""
        if symbol:
            quote = await data_aggregator.get_stock_data(symbol)
            if "error" not in quote:
                indicators = await get_technical_indicators(symbol)
                context = f"""
Stock: {symbol}
Price: ₹{quote.get('price', 0)}
Change: {quote.get('change_pct', 0)}%
RSI: {indicators.get('rsi', 'N/A')}
MACD: {indicators.get('macd', {}).get('signal_type', 'N/A')}
"""
        
        # Get AI response
        ai_response = await ai_client.answer_question(question, context)
        
        if ai_response:
            response = f"🤖 <b>AI Answer:</b>\n\n{ai_response}"
            await message.answer(response)
        else:
            await message.answer(
                "❌ Sorry, I couldn't process your question.\n\n"
                "Try using specific commands like /quote, /ta, /ai"
            )
        
    except Exception as e:
        logger.error(f"Error handling question: {e}")
