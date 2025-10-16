"""
Alpha Vantage API Client
Backup data source for stock market data
"""
import logging
from typing import Optional, Dict, Any
import aiohttp
from datetime import datetime

from config.settings import settings
from config.constants import NSE_SUFFIX

logger = logging.getLogger(__name__)


class AlphaVantageClient:
    """Client for Alpha Vantage API"""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self):
        self.api_key = settings.alpha_vantage_api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.daily_calls = 0
        self.max_daily_calls = 25  # Free tier limit
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Convert to BSE format for Alpha Vantage"""
        symbol = symbol.upper().strip()
        
        # Remove NSE suffix if present
        if symbol.endswith(NSE_SUFFIX):
            symbol = symbol[:-3]
        
        # Add BSE suffix for Indian stocks
        if not symbol.endswith(".BSE"):
            symbol = f"{symbol}.BSE"
        
        return symbol
    
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get global quote (current price and stats)
        
        API: GLOBAL_QUOTE
        """
        if not self.api_key:
            return {"error": "Alpha Vantage API key not configured"}
        
        if self.daily_calls >= self.max_daily_calls:
            return {"error": "Alpha Vantage daily limit exceeded"}
        
        try:
            await self._ensure_session()
            
            normalized_symbol = self._normalize_symbol(symbol)
            
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": normalized_symbol,
                "apikey": self.api_key
            }
            
            async with self.session.get(self.BASE_URL, params=params) as response:
                if response.status != 200:
                    return {"error": f"API returned status {response.status}"}
                
                data = await response.json()
                
                # Increment call counter
                self.daily_calls += 1
                
                if "Global Quote" not in data or not data["Global Quote"]:
                    return {"error": "No data found"}
                
                quote = data["Global Quote"]
                
                price = float(quote.get("05. price", 0))
                change = float(quote.get("09. change", 0))
                change_pct = float(quote.get("10. change percent", "0").replace("%", ""))
                
                return {
                    "symbol": symbol,
                    "normalized_symbol": normalized_symbol,
                    "price": round(price, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "volume": int(quote.get("06. volume", 0)),
                    "open": round(float(quote.get("02. open", 0)), 2),
                    "high": round(float(quote.get("03. high", 0)), 2),
                    "low": round(float(quote.get("04. low", 0)), 2),
                    "previous_close": round(float(quote.get("08. previous close", 0)), 2),
                    "timestamp": quote.get("07. latest trading day"),
                    "source": "alpha_vantage"
                }
                
        except Exception as e:
            logger.error(f"Alpha Vantage error for {symbol}: {e}")
            return {"error": str(e)}
    
    async def get_intraday(
        self,
        symbol: str,
        interval: str = "5min"
    ) -> Optional[Dict[str, Any]]:
        """
        Get intraday time series data
        
        API: TIME_SERIES_INTRADAY
        interval: 1min, 5min, 15min, 30min, 60min
        """
        if not self.api_key:
            return None
        
        try:
            await self._ensure_session()
            
            normalized_symbol = self._normalize_symbol(symbol)
            
            params = {
                "function": "TIME_SERIES_INTRADAY",
                "symbol": normalized_symbol,
                "interval": interval,
                "outputsize": "compact",
                "apikey": self.api_key
            }
            
            async with self.session.get(self.BASE_URL, params=params) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                self.daily_calls += 1
                
                return data
                
        except Exception as e:
            logger.error(f"Alpha Vantage intraday error for {symbol}: {e}")
            return None
    
    async def get_daily(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get daily time series data
        
        API: TIME_SERIES_DAILY
        """
        if not self.api_key:
            return None
        
        try:
            await self._ensure_session()
            
            normalized_symbol = self._normalize_symbol(symbol)
            
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": normalized_symbol,
                "outputsize": "compact",
                "apikey": self.api_key
            }
            
            async with self.session.get(self.BASE_URL, params=params) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                self.daily_calls += 1
                
                return data
                
        except Exception as e:
            logger.error(f"Alpha Vantage daily error for {symbol}: {e}")
            return None
    
    def reset_daily_counter(self):
        """Reset daily API call counter (call at midnight)"""
        self.daily_calls = 0
        logger.info("Alpha Vantage daily counter reset")


# Global instance
alpha_vantage_client = AlphaVantageClient()
