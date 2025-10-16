"""
Watchlist Handler
Manage user's stock watchlist
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, delete, and_
from datetime import datetime

from database.models import Watchlist
from database.connection import db_manager
from services.data.data_aggregator import data_aggregator
from utils.formatters import format_watchlist
from config.settings import settings

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("watchlist"))
async def cmd_watchlist(message: Message):
    """
    Handle /watchlist command
    Subcommands: add, remove, or show
    """
    try:
        parts = message.text.split()
        
        if len(parts) == 1:
            # Show watchlist
            await show_watchlist(message)
            return
        
        subcommand = parts[1].lower()
        
        if subcommand == "add":
            if len(parts) < 3:
                await message.answer("❌ Please provide a symbol\n\nUsage: /watchlist add RELIANCE")
                return
            await add_to_watchlist(message, parts[2].upper())
        
        elif subcommand == "remove":
            if len(parts) < 3:
                await message.answer("❌ Please provide a symbol\n\nUsage: /watchlist remove RELIANCE")
                return
            await remove_from_watchlist(message, parts[2].upper())
        
        else:
            await message.answer(
                "❌ Invalid subcommand\n\n"
                "<b>Usage:</b>\n"
                "/watchlist - Show your watchlist\n"
                "/watchlist add RELIANCE - Add stock\n"
                "/watchlist remove TCS - Remove stock"
            )
    
    except Exception as e:
        logger.error(f"Error in watchlist command: {e}")
        await message.answer("❌ Error processing watchlist command")


async def show_watchlist(message: Message):
    """Display user's watchlist with live prices"""
    try:
        user_id = message.from_user.id
        
        async with db_manager.session() as session:
            result = await session.execute(
                select(Watchlist).where(Watchlist.user_id == user_id)
                .order_by(Watchlist.added_at.desc())
            )
            watchlist_items = result.scalars().all()
            
            if not watchlist_items:
                await message.answer(
                    "📝 <b>Your Watchlist is Empty</b>\n\n"
                    "Add stocks using:\n"
                    "/watchlist add RELIANCE\n"
                    "/watchlist add TCS"
                )
                return
            
            # Fetch live prices for all stocks
            symbols = [item.symbol for item in watchlist_items]
            quotes = await data_aggregator.get_multiple_quotes(symbols)
            
            # Prepare watchlist data with prices
            watchlist_data = []
            for item in watchlist_items:
                quote = quotes.get(item.symbol, {})
                if "error" not in quote:
                    watchlist_data.append({
                        "symbol": item.symbol,
                        "price": quote.get("price", 0),
                        "change_pct": quote.get("change_pct", 0),
                        "added_at": item.added_at
                    })
            
            # Format and send
            formatted_msg = format_watchlist(watchlist_data)
            
            # Add action buttons
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Refresh", callback_data="watchlist_refresh")],
                [InlineKeyboardButton(text="➕ Add Stock", callback_data="watchlist_add_prompt")]
            ])
            
            await message.answer(formatted_msg, reply_markup=keyboard)
    
    except Exception as e:
        logger.error(f"Error showing watchlist: {e}")
        await message.answer("❌ Error fetching watchlist")


async def add_to_watchlist(message: Message, symbol: str):
    """Add a stock to watchlist"""
    try:
        user_id = message.from_user.id
        
        # Validate symbol
        quote = await data_aggregator.get_stock_data(symbol)
        if "error" in quote:
            await message.answer(f"❌ Invalid symbol: {symbol}\n\nPlease check and try again.")
            return
        
        async with db_manager.session() as session:
            # Check if already in watchlist
            result = await session.execute(
                select(Watchlist).where(
                    and_(
                        Watchlist.user_id == user_id,
                        Watchlist.symbol == symbol
                    )
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                await message.answer(f"ℹ️ {symbol} is already in your watchlist")
                return
            
            # Check watchlist size limit
            result = await session.execute(
                select(Watchlist).where(Watchlist.user_id == user_id)
            )
            watchlist_count = len(result.scalars().all())
            
            if watchlist_count >= settings.max_watchlist_size:
                await message.answer(
                    f"❌ Watchlist full ({settings.max_watchlist_size} stocks max)\n\n"
                    f"Remove some stocks first using /watchlist remove SYMBOL"
                )
                return
            
            # Add to watchlist
            new_item = Watchlist(
                user_id=user_id,
                symbol=symbol,
                added_at=datetime.utcnow()
            )
            session.add(new_item)
            await session.commit()
            
            price = quote.get("price", 0)
            change_pct = quote.get("change_pct", 0)
            
            await message.answer(
                f"✅ <b>Added to Watchlist</b>\n\n"
                f"📊 {symbol}\n"
                f"💰 ₹{price:,.2f} ({change_pct:+.2f}%)\n\n"
                f"View your watchlist: /watchlist"
            )
            
            logger.info(f"User {user_id} added {symbol} to watchlist")
    
    except Exception as e:
        logger.error(f"Error adding to watchlist: {e}")
        await message.answer("❌ Error adding to watchlist")


async def remove_from_watchlist(message: Message, symbol: str):
    """Remove a stock from watchlist"""
    try:
        user_id = message.from_user.id
        
        async with db_manager.session() as session:
            result = await session.execute(
                delete(Watchlist).where(
                    and_(
                        Watchlist.user_id == user_id,
                        Watchlist.symbol == symbol
                    )
                ).returning(Watchlist.id)
            )
            
            deleted = result.scalar_one_or_none()
            
            if not deleted:
                await message.answer(f"❌ {symbol} not found in your watchlist")
                return
            
            await session.commit()
            
            await message.answer(
                f"✅ <b>Removed from Watchlist</b>\n\n"
                f"{symbol} has been removed."
            )
            
            logger.info(f"User {user_id} removed {symbol} from watchlist")
    
    except Exception as e:
        logger.error(f"Error removing from watchlist: {e}")
        await message.answer("❌ Error removing from watchlist")


@router.callback_query(F.data == "watchlist_refresh")
async def callback_refresh_watchlist(callback: CallbackQuery):
    """Refresh watchlist prices"""
    try:
        user_id = callback.from_user.id
        
        await callback.answer("Refreshing...")
        
        async with db_manager.session() as session:
            result = await session.execute(
                select(Watchlist).where(Watchlist.user_id == user_id)
            )
            watchlist_items = result.scalars().all()
            
            symbols = [item.symbol for item in watchlist_items]
            quotes = await data_aggregator.get_multiple_quotes(symbols)
            
            watchlist_data = []
            for item in watchlist_items:
                quote = quotes.get(item.symbol, {})
                if "error" not in quote:
                    watchlist_data.append({
                        "symbol": item.symbol,
                        "price": quote.get("price", 0),
                        "change_pct": quote.get("change_pct", 0)
                    })
            
            formatted_msg = format_watchlist(watchlist_data)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Refresh", callback_data="watchlist_refresh")]
            ])
            
            await callback.message.edit_text(formatted_msg, reply_markup=keyboard)
    
    except Exception as e:
        logger.error(f"Error refreshing watchlist: {e}")
        await callback.answer("Error refreshing", show_alert=True)


@router.callback_query(F.data.startswith("watchlist_add:"))
async def callback_add_to_watchlist(callback: CallbackQuery):
    """Quick add to watchlist from stock quote"""
    try:
        symbol = callback.data.split(":")[1]
        user_id = callback.from_user.id
        
        async with db_manager.session() as session:
            # Check if already exists
            result = await session.execute(
                select(Watchlist).where(
                    and_(
                        Watchlist.user_id == user_id,
                        Watchlist.symbol == symbol
                    )
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                await callback.answer(f"{symbol} already in watchlist", show_alert=True)
                return
            
            # Add
            new_item = Watchlist(
                user_id=user_id,
                symbol=symbol,
                added_at=datetime.utcnow()
            )
            session.add(new_item)
            await session.commit()
            
            await callback.answer(f"✅ {symbol} added to watchlist!")
            
            logger.info(f"User {user_id} quick-added {symbol} to watchlist")
    
    except Exception as e:
        logger.error(f"Error in watchlist callback: {e}")
        await callback.answer("Error adding to watchlist", show_alert=True)
