"""
Alert Monitor Background Task
Monitors price alerts and triggers notifications
"""
import logging
import asyncio
from datetime import datetime
from sqlalchemy import select, and_

from database.models import Alert, User, AlertConditionType
from database.connection import db_manager
from services.data.data_aggregator import data_aggregator
from bot.handlers.technical import get_technical_indicators
from config.settings import settings

logger = logging.getLogger(__name__)


class AlertMonitor:
    """Background task to monitor and trigger price alerts"""
    
    def __init__(self):
        self.running = False
        self.check_interval = settings.alert_check_interval_seconds
    
    async def start(self):
        """Start the alert monitor"""
        self.running = True
        logger.info("🔔 Alert monitor started")
        
        while self.running:
            try:
                await self.check_alerts()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in alert monitor: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def stop(self):
        """Stop the alert monitor"""
        self.running = False
        logger.info("🔔 Alert monitor stopped")
    
    async def check_alerts(self):
        """Check all active alerts"""
        try:
            async with db_manager.session() as session:
                # Get all active alerts
                result = await session.execute(
                    select(Alert).where(
                        and_(
                            Alert.is_active == True,
                            Alert.is_triggered == False
                        )
                    )
                )
                alerts = result.scalars().all()
                
                if not alerts:
                    return
                
                logger.info(f"Checking {len(alerts)} active alerts...")
                
                # Get unique symbols
                symbols = list(set(alert.symbol for alert in alerts))
                
                # Fetch quotes for all symbols
                quotes = await data_aggregator.get_multiple_quotes(symbols)
                
                # Check each alert
                for alert in alerts:
                    try:
                        await self.check_single_alert(alert, quotes.get(alert.symbol), session)
                    except Exception as e:
                        logger.error(f"Error checking alert {alert.id}: {e}")
                
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error in check_alerts: {e}")
    
    async def check_single_alert(self, alert: Alert, quote_data: dict, session):
        """Check if a single alert condition is met"""
        if not quote_data or "error" in quote_data:
            return
        
        current_price = quote_data.get("price", 0)
        alert.current_value = current_price
        
        condition_met = False
        message = ""
        
        # Check condition based on type
        if alert.condition_type == AlertConditionType.ABOVE:
            if current_price > alert.target_value:
                condition_met = True
                message = (
                    f"🔔 <b>Alert Triggered!</b>\n\n"
                    f"<b>{alert.symbol}</b> has crossed above ₹{alert.target_value:,.2f}\n\n"
                    f"Current Price: ₹{current_price:,.2f}\n"
                    f"Change: {quote_data.get('change_pct', 0):+.2f}%"
                )
        
        elif alert.condition_type == AlertConditionType.BELOW:
            if current_price < alert.target_value:
                condition_met = True
                message = (
                    f"🔔 <b>Alert Triggered!</b>\n\n"
                    f"<b>{alert.symbol}</b> has crossed below ₹{alert.target_value:,.2f}\n\n"
                    f"Current Price: ₹{current_price:,.2f}\n"
                    f"Change: {quote_data.get('change_pct', 0):+.2f}%"
                )
        
        elif alert.condition_type == AlertConditionType.RSI_BELOW:
            # Get RSI
            indicators = await get_technical_indicators(alert.symbol)
            rsi = indicators.get("rsi")
            if rsi and rsi < alert.target_value:
                condition_met = True
                message = (
                    f"🔔 <b>RSI Alert Triggered!</b>\n\n"
                    f"<b>{alert.symbol}</b> RSI dropped below {alert.target_value}\n\n"
                    f"Current RSI: {rsi}\n"
                    f"Price: ₹{current_price:,.2f}"
                )
        
        elif alert.condition_type == AlertConditionType.RSI_ABOVE:
            indicators = await get_technical_indicators(alert.symbol)
            rsi = indicators.get("rsi")
            if rsi and rsi > alert.target_value:
                condition_met = True
                message = (
                    f"🔔 <b>RSI Alert Triggered!</b>\n\n"
                    f"<b>{alert.symbol}</b> RSI went above {alert.target_value}\n\n"
                    f"Current RSI: {rsi}\n"
                    f"Price: ₹{current_price:,.2f}"
                )
        
        elif alert.condition_type == AlertConditionType.VOLUME_SPIKE:
            volume_ratio = quote_data.get("volume", 0) / quote_data.get("average_volume", 1)
            if volume_ratio > alert.target_value:
                condition_met = True
                message = (
                    f"🔔 <b>Volume Spike Alert!</b>\n\n"
                    f"<b>{alert.symbol}</b> volume spike detected\n\n"
                    f"Volume: {volume_ratio:.2f}x average\n"
                    f"Price: ₹{current_price:,.2f}"
                )
        
        # If condition met, trigger alert
        if condition_met:
            alert.is_triggered = True
            alert.triggered_at = datetime.utcnow()
            alert.message = message
            
            # Send notification
            await self.send_alert_notification(alert.user_id, message)
            
            logger.info(f"Alert {alert.id} triggered for user {alert.user_id}")
    
    async def send_alert_notification(self, user_id: int, message: str):
        """Send alert notification to user"""
        try:
            from aiogram import Bot
            from config.settings import settings
            
            bot = Bot(token=settings.telegram_bot_token)
            
            await bot.send_message(
                user_id,
                message + "\n\n⚠️ <i>Alert has been automatically disabled.</i>"
            )
            
            await bot.session.close()
            
        except Exception as e:
            logger.error(f"Error sending alert notification to user {user_id}: {e}")


# Global instance
alert_monitor = AlertMonitor()
