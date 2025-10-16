"""
Daily Digest Background Task
Send morning and closing market summaries
"""
import logging
import asyncio
from datetime import datetime, time
import pytz
from sqlalchemy import select

from database.models import User
from database.connection import db_manager
from services.data.data_aggregator import data_aggregator
from services.ai.openrouter_client import ai_client
from services.news.news_fetcher import news_fetcher
from config.constants import INDICES, NIFTY_50_SYMBOLS
from config.settings import settings

logger = logging.getLogger(__name__)


class DailyDigest:
    """Send daily market digests"""
    
    def __init__(self):
        self.running = False
        self.tz = pytz.timezone(settings.timezone)
    
    async def start(self):
        """Start the daily digest scheduler"""
        self.running = True
        logger.info("📰 Daily digest scheduler started")
        
        while self.running:
            try:
                now = datetime.now(self.tz)
                
                # Morning digest at 9:15 AM
                morning_time = time(9, 15)
                if now.time().hour == morning_time.hour and now.time().minute == morning_time.minute:
                    await self.send_morning_digest()
                    await asyncio.sleep(60)  # Wait a minute to avoid duplicate
                
                # Closing digest at 3:30 PM
                closing_time = time(15, 30)
                if now.time().hour == closing_time.hour and now.time().minute == closing_time.minute:
                    await self.send_closing_digest()
                    await asyncio.sleep(60)
                
                # Check every 30 seconds
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in daily digest: {e}")
                await asyncio.sleep(30)
    
    async def stop(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("📰 Daily digest scheduler stopped")
    
    async def send_morning_digest(self):
        """Send morning market digest"""
        try:
            logger.info("📰 Preparing morning digest...")
            
            # Get indices data
            nifty = await data_aggregator.get_stock_data("^NSEI")
            sensex = await data_aggregator.get_stock_data("^BSESN")
            
            # Get top news
            news = await news_fetcher.get_market_news()
            headlines = [article.get("title") for article in news[:5]]
            
            # Format message
            message = f"""
🌅 <b>Good Morning! Market Digest</b>

📊 <b>Indices Opening:</b>
NIFTY 50: {nifty.get('price', 0):,.2f} ({nifty.get('change_pct', 0):+.2f}%)
SENSEX: {sensex.get('price', 0):,.2f} ({sensex.get('change_pct', 0):+.2f}%)

📰 <b>Top Headlines:</b>
"""
            
            for i, headline in enumerate(headlines, 1):
                message += f"{i}. {headline}\n"
            
            message += "\n💡 <i>Good luck with your trades today!</i>"
            
            # Send to subscribed users
            await self.send_to_subscribers(message)
            
            logger.info("✅ Morning digest sent")
            
        except Exception as e:
            logger.error(f"Error sending morning digest: {e}")
    
    async def send_closing_digest(self):
        """Send closing market digest"""
        try:
            logger.info("📰 Preparing closing digest...")
            
            # Get indices performance
            nifty = await data_aggregator.get_stock_data("^NSEI")
            sensex = await data_aggregator.get_stock_data("^BSESN")
            
            # Get top gainers/losers (simplified - would need more data)
            message = f"""
🌆 <b>Market Closing Summary</b>

📊 <b>Index Performance:</b>
NIFTY 50: {nifty.get('price', 0):,.2f} ({nifty.get('change_pct', 0):+.2f}%)
   High: {nifty.get('high', 0):,.2f} | Low: {nifty.get('low', 0):,.2f}

SENSEX: {sensex.get('price', 0):,.2f} ({sensex.get('change_pct', 0):+.2f}%)
   High: {sensex.get('high', 0):,.2f} | Low: {sensex.get('low', 0):,.2f}

📈 <b>Market Mood:</b>
"""
            
            # Add AI summary if enabled
            if settings.enable_ai_analysis:
                summary = await ai_client.answer_question(
                    "Summarize today's Indian market performance in 2-3 sentences",
                    context=f"NIFTY: {nifty.get('change_pct', 0)}%, SENSEX: {sensex.get('change_pct', 0)}%"
                )
                if summary:
                    message += f"\n{summary}\n"
            
            message += "\n💼 <i>See you tomorrow! Happy investing!</i>"
            
            # Send to subscribers
            await self.send_to_subscribers(message)
            
            logger.info("✅ Closing digest sent")
            
        except Exception as e:
            logger.error(f"Error sending closing digest: {e}")
    
    async def send_to_subscribers(self, message: str):
        """Send message to all users with digest enabled"""
        try:
            async with db_manager.session() as session:
                result = await session.execute(
                    select(User).where(
                        User.enable_daily_digest == True,
                        User.is_active == True
                    )
                )
                users = result.scalars().all()
                
                if not users:
                    logger.info("No users subscribed to daily digest")
                    return
                
                from aiogram import Bot
                bot = Bot(token=settings.telegram_bot_token)
                
                sent_count = 0
                for user in users:
                    try:
                        await bot.send_message(user.id, message)
                        sent_count += 1
                    except Exception as e:
                        logger.error(f"Error sending to user {user.id}: {e}")
                
                await bot.session.close()
                
                logger.info(f"Sent digest to {sent_count}/{len(users)} users")
                
        except Exception as e:
            logger.error(f"Error sending to subscribers: {e}")


# Global instance
daily_digest = DailyDigest()
