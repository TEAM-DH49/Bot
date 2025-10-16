"""
Scanner Engine Background Task
Auto-scan stocks for trading opportunities
"""
import logging
import asyncio
from datetime import datetime, time
from typing import List, Dict, Any
from sqlalchemy import select

from database.models import User, SignalLog, SignalType
from database.connection import db_manager
from services.data.data_aggregator import data_aggregator
from bot.handlers.technical import get_technical_indicators
from config.constants import NIFTY_50_SYMBOLS
from config.settings import settings
from utils.formatters import format_scanner_results

logger = logging.getLogger(__name__)


class ScannerEngine:
    """Background scanner for stock opportunities"""
    
    def __init__(self):
        self.running = False
        self.scan_interval = settings.scanner_interval_minutes * 60  # Convert to seconds
        self.last_scan = None
    
    async def start(self):
        """Start the scanner engine"""
        self.running = True
        logger.info("🔍 Scanner engine started")
        
        while self.running:
            try:
                # Only scan during market hours
                if settings.is_market_open():
                    await self.run_scan()
                else:
                    logger.info("Market closed, skipping scan")
                
                # Wait for next scan
                self.last_scan = datetime.now()
                await asyncio.sleep(self.scan_interval)
                
            except Exception as e:
                logger.error(f"Error in scanner engine: {e}")
                await asyncio.sleep(self.scan_interval)
    
    async def stop(self):
        """Stop the scanner engine"""
        self.running = False
        logger.info("🔍 Scanner engine stopped")
    
    async def run_scan(self):
        """Run a full market scan"""
        try:
            logger.info(f"🔍 Starting market scan at {datetime.now()}")
            
            signals = []
            
            # Scan all NIFTY 50 stocks
            for symbol in NIFTY_50_SYMBOLS:
                try:
                    symbol_signals = await self.scan_symbol(symbol)
                    signals.extend(symbol_signals)
                except Exception as e:
                    logger.error(f"Error scanning {symbol}: {e}")
            
            logger.info(f"🔍 Scan complete. Found {len(signals)} signals")
            
            # Save signals to database
            await self.save_signals(signals)
            
            # Notify subscribed users
            if signals:
                await self.notify_users(signals)
            
        except Exception as e:
            logger.error(f"Error in run_scan: {e}")
    
    async def scan_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        """Scan a single symbol for signals"""
        signals = []
        
        try:
            # Get quote
            quote = await data_aggregator.get_stock_data(symbol)
            if "error" in quote:
                return signals
            
            price = quote.get("price", 0)
            
            # Get indicators
            indicators = await get_technical_indicators(symbol)
            
            rsi = indicators.get("rsi")
            macd = indicators.get("macd", {})
            volume_analysis = indicators.get("volume", {})
            
            # Check for RSI oversold
            if rsi and rsi < settings.scanner_rsi_oversold:
                signals.append({
                    "symbol": symbol,
                    "signal_type": SignalType.RSI_OVERSOLD,
                    "price": price,
                    "rsi": rsi,
                    "description": f"RSI at {rsi} - Oversold zone"
                })
            
            # Check for RSI overbought
            if rsi and rsi > settings.scanner_rsi_overbought:
                signals.append({
                    "symbol": symbol,
                    "signal_type": SignalType.RSI_OVERBOUGHT,
                    "price": price,
                    "rsi": rsi,
                    "description": f"RSI at {rsi} - Overbought zone"
                })
            
            # Check for MACD bullish crossover
            if macd.get("crossover") == "BULLISH_CROSSOVER":
                signals.append({
                    "symbol": symbol,
                    "signal_type": SignalType.MACD_BULLISH,
                    "price": price,
                    "macd": macd.get("macd_line"),
                    "description": "MACD bullish crossover detected"
                })
            
            # Check for MACD bearish crossover
            if macd.get("crossover") == "BEARISH_CROSSOVER":
                signals.append({
                    "symbol": symbol,
                    "signal_type": SignalType.MACD_BEARISH,
                    "price": price,
                    "macd": macd.get("macd_line"),
                    "description": "MACD bearish crossover detected"
                })
            
            # Check for volume spike
            if volume_analysis.get("is_spike"):
                signals.append({
                    "symbol": symbol,
                    "signal_type": SignalType.VOLUME_SPIKE,
                    "price": price,
                    "volume": volume_analysis.get("current_volume"),
                    "description": f"Volume spike: {volume_analysis.get('volume_ratio')}x average"
                })
            
            # Check for 52-week high breakout
            if price >= quote.get("fifty_two_week_high", 0) * 0.995:  # Within 0.5%
                signals.append({
                    "symbol": symbol,
                    "signal_type": SignalType.BREAKOUT,
                    "price": price,
                    "description": "Near 52-week high - Potential breakout"
                })
            
        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}")
        
        return signals
    
    async def save_signals(self, signals: List[Dict[str, Any]]):
        """Save signals to database"""
        try:
            async with db_manager.session() as session:
                for signal in signals:
                    log = SignalLog(
                        symbol=signal["symbol"],
                        signal_type=signal["signal_type"],
                        price=signal["price"],
                        rsi=signal.get("rsi"),
                        macd=signal.get("macd"),
                        volume=signal.get("volume"),
                        description=signal.get("description"),
                        timestamp=datetime.utcnow()
                    )
                    session.add(log)
                
                await session.commit()
                logger.info(f"Saved {len(signals)} signals to database")
                
        except Exception as e:
            logger.error(f"Error saving signals: {e}")
    
    async def notify_users(self, signals: List[Dict[str, Any]]):
        """Notify users who have scanner enabled"""
        try:
            async with db_manager.session() as session:
                # Get users with scanner enabled
                result = await session.execute(
                    select(User).where(
                        User.enable_scanner_alerts == True,
                        User.is_active == True
                    )
                )
                users = result.scalars().all()
                
                if not users:
                    return
                
                # Format message
                message = format_scanner_results(signals)
                
                # Send to each user
                from aiogram import Bot
                bot = Bot(token=settings.telegram_bot_token)
                
                for user in users:
                    try:
                        await bot.send_message(user.id, message)
                        logger.info(f"Sent scanner results to user {user.id}")
                    except Exception as e:
                        logger.error(f"Error sending to user {user.id}: {e}")
                
                await bot.session.close()
                
        except Exception as e:
            logger.error(f"Error notifying users: {e}")


# Global instance
scanner_engine = ScannerEngine()
