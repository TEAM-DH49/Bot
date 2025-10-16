"""
Technical Analysis Handler
Handle technical analysis requests
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import pandas as pd

from services.data.data_aggregator import data_aggregator
from services.indicators.rsi import calculate_rsi, get_rsi_signal
from services.indicators.macd import calculate_macd, get_macd_signal
from services.indicators.bollinger_bands import calculate_bollinger_bands
from services.indicators.pivot_points import calculate_pivot_points, get_pivot_analysis
from services.indicators.ema import calculate_multiple_emas, get_price_ema_position
from services.indicators.volume_analysis import analyze_volume
from utils.formatters import format_technical_analysis
from database.redis_client import redis_client

logger = logging.getLogger(__name__)

router = Router()


async def get_technical_indicators(symbol: str) -> dict:
    """
    Calculate all technical indicators for a symbol
    
    Returns:
        Dict with all indicators
    """
    try:
        # Check cache first
        cached = await redis_client.get_indicators_cache(symbol)
        if cached:
            logger.info(f"Using cached indicators for {symbol}")
            return cached
        
        # Fetch historical data
        df = await data_aggregator.get_historical_data(symbol, period="3mo", interval="1d")
        
        if df is None or df.empty:
            return {"error": "Unable to fetch historical data"}
        
        # Get current quote
        quote = await data_aggregator.get_stock_data(symbol)
        current_price = quote.get("price", 0)
        
        # Extract price series
        close_prices = df['close']
        high_prices = df['high']
        low_prices = df['low']
        volume = df['volume']
        
        indicators = {}
        
        # RSI
        rsi = calculate_rsi(close_prices)
        if rsi:
            indicators['rsi'] = rsi
            indicators['rsi_signal'] = get_rsi_signal(rsi)
        
        # MACD
        macd = calculate_macd(close_prices)
        if macd:
            indicators['macd'] = macd
            indicators['macd_signal'] = get_macd_signal(macd)
        
        # EMAs
        emas = calculate_multiple_emas(close_prices, [20, 50, 200])
        if emas:
            indicators['emas'] = emas
            indicators['ema_position'] = get_price_ema_position(current_price, emas)
        
        # Bollinger Bands
        bb = calculate_bollinger_bands(close_prices)
        if bb:
            indicators['bollinger'] = bb
        
        # Pivot Points (using yesterday's data)
        if len(df) >= 2:
            yesterday = df.iloc[-2]
            pivots = calculate_pivot_points(
                yesterday['high'],
                yesterday['low'],
                yesterday['close']
            )
            if pivots:
                indicators['pivots'] = pivots
                indicators['pivot_analysis'] = get_pivot_analysis(current_price, pivots)
        
        # Volume Analysis
        vol_analysis = analyze_volume(volume, close_prices)
        if vol_analysis and 'error' not in vol_analysis:
            indicators['volume'] = vol_analysis
        
        # Cache for 5 minutes
        await redis_client.set_indicators_cache(symbol, indicators)
        
        return indicators
        
    except Exception as e:
        logger.error(f"Error calculating indicators for {symbol}: {e}")
        return {"error": str(e)}


@router.message(Command("ta"))
async def cmd_technical_analysis(message: Message):
    """
    Handle /ta command for technical analysis
    Usage: /ta RELIANCE
    """
    try:
        parts = message.text.split()
        
        if len(parts) < 2:
            await message.answer(
                "❌ Please provide a stock symbol\n\n"
                "Usage: /ta RELIANCE\n"
                "Example: /ta TCS"
            )
            return
        
        symbol = parts[1].upper().strip()
        
        # Send status message
        status_msg = await message.answer(f"📊 Calculating technical indicators for {symbol}...")
        
        # Get indicators
        indicators = await get_technical_indicators(symbol)
        
        # Check for errors
        if "error" in indicators:
            await status_msg.edit_text(
                f"❌ {indicators['error']}\n\n"
                f"Unable to calculate indicators for {symbol}"
            )
            return
        
        # Format message
        formatted_msg = format_technical_analysis(symbol, indicators)
        
        # Create keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Refresh", callback_data=f"ta:{symbol}"),
                InlineKeyboardButton(text="💰 Quote", callback_data=f"quote:{symbol}")
            ],
            [
                InlineKeyboardButton(text="🤖 AI Analysis", callback_data=f"ai:{symbol}"),
                InlineKeyboardButton(text="📈 Patterns", callback_data=f"patterns:{symbol}")
            ],
            [
                InlineKeyboardButton(text="🔔 Set Alert", callback_data=f"alert_set:{symbol}")
            ]
        ])
        
        # Update message
        await status_msg.edit_text(formatted_msg, reply_markup=keyboard)
        
        # Add disclaimer
        await message.answer(
            "⚠️ <i>Technical analysis is educational only. Not financial advice.</i>"
        )
        
        logger.info(f"Sent technical analysis for {symbol} to user {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error in technical analysis command: {e}")
        await message.answer("❌ An error occurred. Please try again later.")


@router.callback_query(F.data.startswith("ta:"))
async def callback_refresh_ta(callback: CallbackQuery):
    """Handle technical analysis refresh callback"""
    try:
        symbol = callback.data.split(":")[1]
        
        await callback.answer("Refreshing indicators...")
        
        # Clear cache and get fresh data
        await redis_client.delete(f"indicators:{symbol}")
        indicators = await get_technical_indicators(symbol)
        
        if "error" in indicators:
            await callback.message.edit_text(f"❌ Error: {indicators['error']}")
            return
        
        # Format and update
        formatted_msg = format_technical_analysis(symbol, indicators)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Refresh", callback_data=f"ta:{symbol}"),
                InlineKeyboardButton(text="💰 Quote", callback_data=f"quote:{symbol}")
            ],
            [
                InlineKeyboardButton(text="🤖 AI Analysis", callback_data=f"ai:{symbol}"),
                InlineKeyboardButton(text="📈 Patterns", callback_data=f"patterns:{symbol}")
            ]
        ])
        
        await callback.message.edit_text(formatted_msg, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in TA callback: {e}")
        await callback.answer("Error refreshing", show_alert=True)


@router.message(Command("timeframe"))
async def cmd_timeframe_analysis(message: Message):
    """
    Multi-timeframe analysis
    Usage: /timeframe RELIANCE
    """
    try:
        parts = message.text.split()
        
        if len(parts) < 2:
            await message.answer("❌ Please provide a symbol\n\nUsage: /timeframe RELIANCE")
            return
        
        symbol = parts[1].upper().strip()
        
        status_msg = await message.answer(f"⏱️ Analyzing {symbol} across multiple timeframes...")
        
        # Fetch different timeframes
        timeframes = {
            "1 Day": await data_aggregator.get_intraday_data(symbol, "5m"),
            "1 Week": await data_aggregator.get_historical_data(symbol, "5d", "1h"),
            "1 Month": await data_aggregator.get_historical_data(symbol, "1mo", "1d"),
            "3 Months": await data_aggregator.get_historical_data(symbol, "3mo", "1d"),
        }
        
        response = f"⏱️ <b>Multi-Timeframe Analysis: {symbol}</b>\n\n"
        
        for timeframe, df in timeframes.items():
            if df is None or df.empty:
                response += f"<b>{timeframe}:</b> No data\n\n"
                continue
            
            # Calculate RSI for each timeframe
            rsi = calculate_rsi(df['close'])
            rsi_signal = get_rsi_signal(rsi) if rsi else {}
            
            emoji = rsi_signal.get('emoji', '⚪')
            signal = rsi_signal.get('signal', 'N/A')
            
            response += f"<b>{timeframe}:</b>\n"
            response += f"   RSI: {rsi} {emoji}\n"
            response += f"   Signal: {signal}\n\n"
        
        response += "⚠️ <i>Educational purpose only</i>"
        
        await status_msg.edit_text(response)
        
    except Exception as e:
        logger.error(f"Error in timeframe analysis: {e}")
        await message.answer("❌ Error performing timeframe analysis")
