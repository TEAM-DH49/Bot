"""
Yahoo Finance Data Client
Primary data source for Indian stock market data
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd

from config.constants import NSE_SUFFIX, SYMBOL_CORRECTIONS
from database.redis_client import redis_client

logger = logging.getLogger(__name__)


class YahooFinanceClient:
    """Client for fetching stock data from Yahoo Finance"""
    
    def __init__(self):
        self.session = None
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to Yahoo Finance format"""
        symbol = symbol.upper().strip()
        
        # Apply corrections
        symbol = SYMBOL_CORRECTIONS.get(symbol, symbol)
        
        # Add NSE suffix if not present
        if not symbol.endswith(NSE_SUFFIX) and not symbol.endswith(".BO"):
            symbol = f"{symbol}{NSE_SUFFIX}"
        
        return symbol
    
    async def get_live_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time stock quote
        
        Returns:
            dict with: symbol, price, change, change_pct, volume, open, high, low, close
        """
        try:
            # Check cache first
            cache_key = f"quote:{symbol}"
            cached = await redis_client.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {symbol}")
                return cached
            
            normalized_symbol = self._normalize_symbol(symbol)
            ticker = yf.Ticker(normalized_symbol)
            
            # Get current data
            info = ticker.info
            
            if not info or "regularMarketPrice" not in info:
                return {"error": f"No data found for {symbol}"}
            
            # Extract relevant data
            current_price = info.get("regularMarketPrice", 0)
            previous_close = info.get("regularMarketPreviousClose", 0)
            change = current_price - previous_close if previous_close else 0
            change_pct = (change / previous_close * 100) if previous_close else 0
            
            result = {
                "symbol": symbol,
                "normalized_symbol": normalized_symbol,
                "price": round(current_price, 2),
                "previous_close": round(previous_close, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "volume": info.get("regularMarketVolume", 0),
                "open": round(info.get("regularMarketOpen", 0), 2),
                "high": round(info.get("regularMarketDayHigh", 0), 2),
                "low": round(info.get("regularMarketDayLow", 0), 2),
                "market_cap": info.get("marketCap", 0),
                "fifty_two_week_high": round(info.get("fiftyTwoWeekHigh", 0), 2),
                "fifty_two_week_low": round(info.get("fiftyTwoWeekLow", 0), 2),
                "average_volume": info.get("averageDailyVolume10Day", 0),
                "pe_ratio": round(info.get("trailingPE", 0), 2) if info.get("trailingPE") else None,
                "timestamp": datetime.now().isoformat(),
                "source": "yahoo_finance"
            }
            
            # Cache result
            await redis_client.set_quote_cache(symbol, result)
            
            logger.info(f"Fetched quote for {symbol}: ₹{current_price}")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return {"error": str(e), "symbol": symbol}
    
    async def get_historical_data(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """
        Get historical OHLCV data
        
        Args:
            symbol: Stock symbol
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            ticker = yf.Ticker(normalized_symbol)
            
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"No historical data for {symbol}")
                return None
            
            # Clean data
            df = df.reset_index()
            df.columns = [col.lower() for col in df.columns]
            
            logger.info(f"Fetched {len(df)} data points for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    async def get_intraday_data(self, symbol: str, interval: str = "5m") -> Optional[pd.DataFrame]:
        """
        Get intraday data for today
        
        Args:
            symbol: Stock symbol
            interval: Time interval (1m, 2m, 5m, 15m, 30m, 60m, 90m)
        
        Returns:
            DataFrame with intraday OHLCV data
        """
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            ticker = yf.Ticker(normalized_symbol)
            
            # Get 1 day of intraday data
            df = ticker.history(period="1d", interval=interval)
            
            if df.empty:
                logger.warning(f"No intraday data for {symbol}")
                return None
            
            df = df.reset_index()
            df.columns = [col.lower() for col in df.columns]
            
            logger.info(f"Fetched intraday data for {symbol}: {len(df)} points")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching intraday data for {symbol}: {e}")
            return None
    
    async def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """Get company information"""
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            ticker = yf.Ticker(normalized_symbol)
            info = ticker.info
            
            return {
                "name": info.get("longName", symbol),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "website": info.get("website"),
                "description": info.get("longBusinessSummary"),
                "employees": info.get("fullTimeEmployees"),
                "city": info.get("city"),
                "state": info.get("state"),
                "country": info.get("country"),
            }
            
        except Exception as e:
            logger.error(f"Error fetching company info for {symbol}: {e}")
            return {"error": str(e)}
    
    async def get_index_data(self, index_symbol: str) -> Dict[str, Any]:
        """Get Indian market index data"""
        try:
            ticker = yf.Ticker(index_symbol)
            info = ticker.info
            
            current_price = info.get("regularMarketPrice", 0)
            previous_close = info.get("regularMarketPreviousClose", 0)
            change = current_price - previous_close
            change_pct = (change / previous_close * 100) if previous_close else 0
            
            return {
                "symbol": index_symbol,
                "name": info.get("shortName", index_symbol),
                "price": round(current_price, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "open": round(info.get("regularMarketOpen", 0), 2),
                "high": round(info.get("regularMarketDayHigh", 0), 2),
                "low": round(info.get("regularMarketDayLow", 0), 2),
                "volume": info.get("regularMarketVolume", 0),
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error fetching index data for {index_symbol}: {e}")
            return {"error": str(e)}


# Global instance
yahoo_client = YahooFinanceClient()
