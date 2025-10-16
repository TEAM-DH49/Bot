"""
Alerts Handler
Manage price and indicator alerts
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, and_, delete
from datetime import datetime

from database.models import Alert, AlertConditionType
from database.connection import db_manager
from config.settings import settings

logger = logging.getLogger(__name__)

router = Router()


class AlertStates(StatesGroup):
    """States for alert creation"""
    waiting_for_details = State()


@router.message(Command("alert"))
async def cmd_alert(message: Message):
    """
    Handle /alert command
    Subcommands: add, list, delete
    """
    try:
        parts = message.text.split()
        
        if len(parts) == 1:
            # Show alert menu
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Add Alert", callback_data="alert_menu_add")],
                [InlineKeyboardButton(text="📋 List Alerts", callback_data="alert_menu_list")],
                [InlineKeyboardButton(text="📚 Alert Guide", callback_data="alert_menu_help")]
            ])
            
            await message.answer(
                "🔔 <b>Alerts Management</b>\n\n"
                "Choose an option:",
                reply_markup=keyboard
            )
            return
        
        subcommand = parts[1].lower()
        
        if subcommand == "add":
            await handle_add_alert(message, parts[2:])
        elif subcommand == "list":
            await handle_list_alerts(message)
        elif subcommand == "delete":
            if len(parts) < 3:
                await message.answer("❌ Please provide alert ID\n\nUsage: /alert delete 5")
                return
            await handle_delete_alert(message, int(parts[2]))
        else:
            await message.answer(
                "❌ Invalid subcommand\n\n"
                "Usage:\n"
                "/alert add SYMBOL above/below PRICE\n"
                "/alert list\n"
                "/alert delete ID"
            )
    
    except Exception as e:
        logger.error(f"Error in alert command: {e}")
        await message.answer("❌ Error processing alert command")


async def handle_add_alert(message: Message, args: list):
    """Add a new alert"""
    try:
        if len(args) < 3:
            await message.answer(
                "❌ Invalid format\n\n"
                "<b>Usage:</b>\n"
                "/alert add RELIANCE above 2900\n"
                "/alert add TCS below 3800\n"
                "/alert add INFY rsi_below 30"
            )
            return
        
        symbol = args[0].upper()
        condition = args[1].lower()
        target_value = float(args[2])
        
        # Map condition to enum
        condition_map = {
            "above": AlertConditionType.ABOVE,
            "below": AlertConditionType.BELOW,
            "rsi_above": AlertConditionType.RSI_ABOVE,
            "rsi_below": AlertConditionType.RSI_BELOW
        }
        
        if condition not in condition_map:
            await message.answer(
                "❌ Invalid condition\n\n"
                "Valid conditions: above, below, rsi_above, rsi_below"
            )
            return
        
        condition_type = condition_map[condition]
        user_id = message.from_user.id
        
        # Check user's alert count
        async with db_manager.session() as session:
            result = await session.execute(
                select(Alert).where(
                    and_(
                        Alert.user_id == user_id,
                        Alert.is_active == True
                    )
                )
            )
            active_alerts = result.scalars().all()
            
            if len(active_alerts) >= settings.max_alerts:
                await message.answer(
                    f"❌ Maximum alert limit reached ({settings.max_alerts})\n\n"
                    f"Please delete some alerts first using /alert delete ID"
                )
                return
            
            # Create new alert
            new_alert = Alert(
                user_id=user_id,
                symbol=symbol,
                condition_type=condition_type,
                target_value=target_value,
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            session.add(new_alert)
            await session.commit()
            await session.refresh(new_alert)
            
            await message.answer(
                f"✅ <b>Alert Created!</b>\n\n"
                f"🔔 Alert ID: {new_alert.id}\n"
                f"📊 Symbol: {symbol}\n"
                f"⚡ Condition: {condition.replace('_', ' ').title()}\n"
                f"🎯 Target: {target_value}\n\n"
                f"You'll be notified when this condition is met."
            )
            
            logger.info(f"User {user_id} created alert for {symbol}")
    
    except ValueError:
        await message.answer("❌ Invalid target value. Please use a number.")
    except Exception as e:
        logger.error(f"Error adding alert: {e}")
        await message.answer("❌ Error creating alert")


async def handle_list_alerts(message: Message):
    """List all user's alerts"""
    try:
        user_id = message.from_user.id
        
        async with db_manager.session() as session:
            result = await session.execute(
                select(Alert).where(Alert.user_id == user_id)
                .order_by(Alert.created_at.desc())
            )
            alerts = result.scalars().all()
            
            if not alerts:
                await message.answer(
                    "📭 <b>No Alerts</b>\n\n"
                    "You haven't created any alerts yet.\n\n"
                    "Create one with:\n"
                    "/alert add RELIANCE above 2900"
                )
                return
            
            response = f"🔔 <b>Your Alerts ({len(alerts)})</b>\n\n"
            
            for alert in alerts:
                status = "✅ Active" if alert.is_active else "❌ Inactive"
                if alert.is_triggered:
                    status = "🔔 Triggered"
                
                response += (
                    f"<b>ID {alert.id}:</b> {alert.symbol}\n"
                    f"   Condition: {alert.condition_type.value.replace('_', ' ').title()}\n"
                    f"   Target: {alert.target_value}\n"
                    f"   Status: {status}\n"
                    f"   Created: {alert.created_at.strftime('%d-%m-%Y')}\n\n"
                )
            
            response += "To delete: /alert delete ID"
            
            await message.answer(response)
    
    except Exception as e:
        logger.error(f"Error listing alerts: {e}")
        await message.answer("❌ Error fetching alerts")


async def handle_delete_alert(message: Message, alert_id: int):
    """Delete an alert"""
    try:
        user_id = message.from_user.id
        
        async with db_manager.session() as session:
            result = await session.execute(
                select(Alert).where(
                    and_(
                        Alert.id == alert_id,
                        Alert.user_id == user_id
                    )
                )
            )
            alert = result.scalar_one_or_none()
            
            if not alert:
                await message.answer(f"❌ Alert ID {alert_id} not found or doesn't belong to you")
                return
            
            await session.delete(alert)
            await session.commit()
            
            await message.answer(
                f"✅ <b>Alert Deleted</b>\n\n"
                f"Alert ID {alert_id} for {alert.symbol} has been removed."
            )
            
            logger.info(f"User {user_id} deleted alert {alert_id}")
    
    except Exception as e:
        logger.error(f"Error deleting alert: {e}")
        await message.answer("❌ Error deleting alert")


@router.callback_query(F.data.startswith("alert_set:"))
async def callback_set_alert(callback: CallbackQuery):
    """Quick alert setup from stock quote"""
    try:
        symbol = callback.data.split(":")[1]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Above Current Price", callback_data=f"alert_type:{symbol}:above")],
            [InlineKeyboardButton(text="Below Current Price", callback_data=f"alert_type:{symbol}:below")],
            [InlineKeyboardButton(text="RSI Below 30", callback_data=f"alert_quick:{symbol}:rsi_below:30")],
            [InlineKeyboardButton(text="RSI Above 70", callback_data=f"alert_quick:{symbol}:rsi_above:70")]
        ])
        
        await callback.message.answer(
            f"🔔 <b>Create Alert for {symbol}</b>\n\n"
            f"Choose alert type:",
            reply_markup=keyboard
        )
        
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Error in alert callback: {e}")
        await callback.answer("Error", show_alert=True)


@router.callback_query(F.data.startswith("alert_quick:"))
async def callback_quick_alert(callback: CallbackQuery):
    """Quick create alert"""
    try:
        parts = callback.data.split(":")
        symbol = parts[1]
        condition = parts[2]
        target = float(parts[3])
        
        # Create alert
        from database.models import Alert, AlertConditionType
        
        condition_map = {
            "above": AlertConditionType.ABOVE,
            "below": AlertConditionType.BELOW,
            "rsi_above": AlertConditionType.RSI_ABOVE,
            "rsi_below": AlertConditionType.RSI_BELOW
        }
        
        async with db_manager.session() as session:
            alert = Alert(
                user_id=callback.from_user.id,
                symbol=symbol,
                condition_type=condition_map[condition],
                target_value=target,
                is_active=True
            )
            session.add(alert)
            await session.commit()
            
            await callback.message.answer(
                f"✅ Alert created for {symbol}!\n"
                f"Condition: {condition.replace('_', ' ').title()} {target}"
            )
        
        await callback.answer("Alert created!")
    
    except Exception as e:
        logger.error(f"Error in quick alert: {e}")
        await callback.answer("Error creating alert", show_alert=True)
