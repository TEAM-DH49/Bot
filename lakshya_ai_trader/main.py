"""
Lakshya AI Trader - Main Bot Entry Point
Indian Stock Market Telegram Bot with AI-Powered Analysis
"""
import asyncio
import logging
import sys
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config.settings import settings
from database.connection import db_manager
from database.redis_client import redis_client

# Import all handlers
from bot.handlers import start, quote, technical, ai_analysis

# Import middleware
from bot.middleware.rate_limiter import RateLimitMiddleware
from bot.middleware.error_handler import ErrorHandlerMiddleware
from bot.middleware.logging_middleware import LoggingMiddleware

# Import background tasks
from tasks.alert_monitor import AlertMonitor
from tasks.scanner_engine import ScannerEngine
from tasks.daily_digest import DailyDigest

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.log_file)
    ]
)

logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    """Execute on bot startup"""
    try:
        logger.info("=" * 80)
        logger.info("🚀 Starting Lakshya AI Trader Bot")
        logger.info("=" * 80)
        
        # Initialize database
        logger.info("📊 Initializing database...")
        await db_manager.initialize()
        logger.info("✅ Database initialized")
        
        # Initialize Redis
        logger.info("🔴 Initializing Redis...")
        await redis_client.initialize()
        logger.info("✅ Redis initialized")
        
        # Test database health
        db_healthy = await db_manager.health_check()
        redis_healthy = await redis_client.health_check()
        
        if not db_healthy:
            logger.error("❌ Database health check failed")
        if not redis_healthy:
            logger.error("❌ Redis health check failed")
        
        # Start background tasks
        if settings.enable_auto_scanner:
            logger.info("🔍 Starting scanner engine...")
            scanner = ScannerEngine()
            asyncio.create_task(scanner.start())
        
        if settings.enable_daily_digest:
            logger.info("📰 Starting daily digest scheduler...")
            digest = DailyDigest()
            asyncio.create_task(digest.start())
        
        logger.info("🔔 Starting alert monitor...")
        alert_monitor = AlertMonitor()
        asyncio.create_task(alert_monitor.start())
        
        # Get bot info
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot @{bot_info.username} started successfully!")
        logger.info(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🌍 Environment: {settings.environment}")
        logger.info(f"🔧 Debug mode: {settings.debug}")
        logger.info("=" * 80)
        
        # Send startup notification to admins
        for admin_id in settings.admin_ids:
            try:
                await bot.send_message(
                    admin_id,
                    f"✅ <b>Bot Started!</b>\n\n"
                    f"🤖 @{bot_info.username}\n"
                    f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"🌍 Environment: {settings.environment}"
                )
            except:
                pass
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")
        raise


async def on_shutdown(bot: Bot):
    """Execute on bot shutdown"""
    try:
        logger.info("=" * 80)
        logger.info("🛑 Shutting down Lakshya AI Trader Bot")
        logger.info("=" * 80)
        
        # Close database connections
        logger.info("📊 Closing database connections...")
        await db_manager.close()
        
        # Close Redis connections
        logger.info("🔴 Closing Redis connections...")
        await redis_client.close()
        
        # Close AI client
        from services.ai.openrouter_client import ai_client
        await ai_client.close()
        
        # Close data clients
        from services.data.alpha_vantage import alpha_vantage_client
        await alpha_vantage_client.close()
        
        from services.news.news_fetcher import news_fetcher
        await news_fetcher.close()
        
        logger.info("✅ Graceful shutdown completed")
        logger.info(f"⏰ Shutdown at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        
        # Notify admins
        for admin_id in settings.admin_ids:
            try:
                await bot.send_message(
                    admin_id,
                    f"🛑 <b>Bot Stopped</b>\n\n"
                    f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            except:
                pass
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


async def main():
    """Main function to run the bot"""
    try:
        # Initialize bot and dispatcher
        bot = Bot(
            token=settings.telegram_bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        dp = Dispatcher()
        
        # Register middleware
        logger.info("🔧 Registering middleware...")
        dp.message.middleware(LoggingMiddleware())
        dp.message.middleware(RateLimitMiddleware())
        dp.message.middleware(ErrorHandlerMiddleware())
        
        # Register handlers
        logger.info("📝 Registering handlers...")
        dp.include_router(start.router)
        dp.include_router(quote.router)
        dp.include_router(technical.router)
        dp.include_router(ai_analysis.router)
        
        # Register startup/shutdown handlers
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        
        # Start polling
        logger.info("🔄 Starting bot polling...")
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True
        )
        
    except KeyboardInterrupt:
        logger.info("⚠️ Received keyboard interrupt. Shutting down...")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise
    finally:
        logger.info("👋 Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Goodbye!")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
