"""
Stock Quote Handler
Handle stock price quote requests
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from services.data.data_aggregator import data_aggregator
from utils.formatters import format_stock_quote
from config.constants import SYMBOL_CORRECTIONS

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("quote"))
async def cmd_quote(message: Message):
    """
    Handle /quote command
    Usage: /quote RELIANCE or /quote TCS
    """
    try:
        # Extract symbol from command
        parts = message.text.split()
        
        if len(parts) < 2:
            await message.answer(
                "❌ Please provide a stock symbol\n\n"
                "Usage: /quote RELIANCE\n"
                "Or just send: RELIANCE"
            )
            return
        
        symbol = parts[1].upper().strip()
        
        # Apply symbol corrections
        symbol = SYMBOL_CORRECTIONS.get(symbol, symbol)
        
        # Send "fetching" message
        status_msg = await message.answer(f"🔄 Fetching data for {symbol}...")
        
        # Fetch stock data
        data = await data_aggregator.get_stock_data(symbol)
        
        # Check for errors
        if "error" in data:
            await status_msg.edit_text(
                f"❌ {data['error']}\n\n"
                f"Please check the symbol and try again.\n"
                f"Example: /quote RELIANCE"
            )
            return
        
        # Format message
        formatted_msg = format_stock_quote(data)
        
        # Create inline keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Refresh", callback_data=f"quote:{symbol}"),
                InlineKeyboardButton(text="📊 Technical", callback_data=f"ta:{symbol}")
            ],
            [
                InlineKeyboardButton(text="🤖 AI Analysis", callback_data=f"ai:{symbol}"),
                InlineKeyboardButton(text="📰 News", callback_data=f"news:{symbol}")
            ],
            [
                InlineKeyboardButton(text="➕ Watchlist", callback_data=f"watchlist_add:{symbol}"),
                InlineKeyboardButton(text="🔔 Alert", callback_data=f"alert_set:{symbol}")
            ]
        ])
        
        # Update message with stock data
        await status_msg.edit_text(formatted_msg, reply_markup=keyboard)
        
        logger.info(f"Sent quote for {symbol} to user {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error in quote command: {e}")
        await message.answer("❌ An error occurred. Please try again later.")


@router.message(F.text.regexp(r'^[A-Z]{2,15}$'))
async def handle_direct_symbol(message: Message):
    """
    Handle direct symbol input (e.g., just "RELIANCE")
    Matches 2-15 uppercase letters
    """
    try:
        symbol = message.text.upper().strip()
        
        # Apply corrections
        symbol = SYMBOL_CORRECTIONS.get(symbol, symbol)
        
        # Send status message
        status_msg = await message.answer(f"🔄 Fetching {symbol}...")
        
        # Fetch data
        data = await data_aggregator.get_stock_data(symbol)
        
        if "error" in data:
            await status_msg.edit_text(
                f"❌ No data found for {symbol}\n\n"
                f"Try /help to see how to use the bot."
            )
            return
        
        # Format and send
        formatted_msg = format_stock_quote(data)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Refresh", callback_data=f"quote:{symbol}"),
                InlineKeyboardButton(text="📊 Technical", callback_data=f"ta:{symbol}")
            ],
            [
                InlineKeyboardButton(text="🤖 AI Analysis", callback_data=f"ai:{symbol}"),
                InlineKeyboardButton(text="📰 News", callback_data=f"news:{symbol}")
            ],
            [
                InlineKeyboardButton(text="➕ Watchlist", callback_data=f"watchlist_add:{symbol}"),
                InlineKeyboardButton(text="🔔 Alert", callback_data=f"alert_set:{symbol}")
            ]
        ])
        
        await status_msg.edit_text(formatted_msg, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error handling direct symbol: {e}")


@router.callback_query(F.data.startswith("quote:"))
async def callback_refresh_quote(callback: CallbackQuery):
    """Handle quote refresh callback"""
    try:
        symbol = callback.data.split(":")[1]
        
        await callback.answer("Refreshing...")
        
        # Fetch fresh data (force refresh)
        data = await data_aggregator.get_stock_data(symbol, force_refresh=True)
        
        if "error" in data:
            await callback.message.edit_text(f"❌ Error fetching {symbol}")
            return
        
        # Format and update
        formatted_msg = format_stock_quote(data)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Refresh", callback_data=f"quote:{symbol}"),
                InlineKeyboardButton(text="📊 Technical", callback_data=f"ta:{symbol}")
            ],
            [
                InlineKeyboardButton(text="🤖 AI Analysis", callback_data=f"ai:{symbol}"),
                InlineKeyboardButton(text="📰 News", callback_data=f"news:{symbol}")
            ],
            [
                InlineKeyboardButton(text="➕ Watchlist", callback_data=f"watchlist_add:{symbol}"),
                InlineKeyboardButton(text="🔔 Alert", callback_data=f"alert_set:{symbol}")
            ]
        ])
        
        await callback.message.edit_text(formatted_msg, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in quote callback: {e}")
        await callback.answer("Error refreshing", show_alert=True)


@router.message(F.text.regexp(r'^[A-Z]{2,15}(?:\s*,\s*[A-Z]{2,15})+$'))
async def handle_multiple_symbols(message: Message):
    """
    Handle multiple symbols (e.g., "RELIANCE, TCS, INFY")
    """
    try:
        # Parse symbols
        symbols = [s.strip().upper() for s in message.text.split(',')]
        symbols = [SYMBOL_CORRECTIONS.get(s, s) for s in symbols]
        
        # Limit to 10 symbols
        if len(symbols) > 10:
            await message.answer("❌ Please limit to 10 symbols at a time")
            return
        
        await message.answer(f"🔄 Fetching data for {len(symbols)} stocks...")
        
        # Fetch all quotes
        results = await data_aggregator.get_multiple_quotes(symbols)
        
        # Format response
        response = "<b>📊 Multiple Quotes</b>\n\n"
        
        for symbol, data in results.items():
            if "error" in data:
                response += f"❌ <b>{symbol}:</b> Not found\n\n"
            else:
                price = data.get("price", 0)
                change_pct = data.get("change_pct", 0)
                emoji = "🟢" if change_pct > 0 else "🔴" if change_pct < 0 else "⚪"
                response += f"{emoji} <b>{symbol}:</b> ₹{price:,.2f} ({change_pct:+.2f}%)\n\n"
        
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"Error handling multiple symbols: {e}")
        await message.answer("❌ Error processing symbols")
