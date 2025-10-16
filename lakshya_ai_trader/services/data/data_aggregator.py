"""
Data Aggregator with Multi-Source Fallback
Intelligently fetches data from multiple sources with fallback logic
"""
import logging
from typing import Dict, Any, Optional
import pandas as pd

from services.data.yahoo_finance import yahoo_client
from services.data.alpha_vantage import alpha_vantage_client
from services.data.finnhub_client import finnhub_client
from database.redis_client import redis_client

logger = logging.getLogger(__name__)


class DataAggregator:
    """
    Smart data aggregator with multi-source fallback
    
    Priority:
    1. Yahoo Finance (unlimited, fast)
    2. Alpha Vantage (25/day limit)
    3. Finnhub (60/min limit)
    """
    
    def __init__(self):
        self.sources = [
            ("yahoo_finance", yahoo_client),
            ("alpha_vantage", alpha_vantage_client),
            ("finnhub", finnhub_client),
        ]
    
    async def get_stock_data(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get stock data with intelligent fallback
        
        Args:
            symbol: Stock symbol
            force_refresh: Skip cache and fetch fresh data
        
        Returns:
            Stock data dict or error dict
        """
        # Check cache first
        if not force_refresh:
            cached = await redis_client.get_quote_cache(symbol)
            if cached and "error" not in cached:
                logger.debug(f"Returning cached data for {symbol}")
                return cached
        
        # Try each source in order
        for source_name, client in self.sources:
            try:
                logger.info(f"Trying {source_name} for {symbol}")
                
                if source_name == "yahoo_finance":
                    data = await client.get_live_quote(symbol)
                elif source_name == "alpha_vantage":
                    data = await client.get_quote(symbol)
                elif source_name == "finnhub":
                    data = await client.get_quote(symbol)
                else:
                    continue
                
                # Check if data is valid
                if data and "error" not in data and data.get("price", 0) > 0:
                    logger.info(f"Successfully fetched {symbol} from {source_name}")
                    
                    # Cache the result
                    await redis_client.set_quote_cache(symbol, data)
                    
                    return data
                
                logger.warning(f"{source_name} returned invalid data for {symbol}")
                
            except Exception as e:
                logger.error(f"Error with {source_name} for {symbol}: {e}")
                continue
        
        # All sources failed
        logger.error(f"All data sources failed for {symbol}")
        return {
            "error": f"Unable to fetch data for {symbol}. All sources failed.",
            "symbol": symbol
        }
    
    async def get_historical_data(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """
        Get historical OHLCV data
        
        Currently only Yahoo Finance supports this reliably
        """
        try:
            df = await yahoo_client.get_historical_data(symbol, period, interval)
            
            if df is not None and not df.empty:
                return df
            
            logger.warning(f"No historical data available for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    async def get_intraday_data(
        self,
        symbol: str,
        interval: str = "5m"
    ) -> Optional[pd.DataFrame]:
        """Get intraday data"""
        try:
            df = await yahoo_client.get_intraday_data(symbol, interval)
            
            if df is not None and not df.empty:
                return df
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching intraday data for {symbol}: {e}")
            return None
    
    async def get_multiple_quotes(self, symbols: list[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get quotes for multiple symbols
        
        Returns:
            Dict mapping symbol to quote data
        """
        results = {}
        
        for symbol in symbols:
            try:
                data = await self.get_stock_data(symbol)
                results[symbol] = data
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
                results[symbol] = {"error": str(e)}
        
        return results
    
    async def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """Get company information"""
        try:
            # Try Yahoo Finance first
            info = await yahoo_client.get_company_info(symbol)
            
            if info and "error" not in info:
                return info
            
            return {"error": "Company info not available"}
            
        except Exception as e:
            logger.error(f"Error fetching company info for {symbol}: {e}")
            return {"error": str(e)}
    
    async def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if symbol exists
        
        Returns:
            True if symbol is valid
        """
        try:
            data = await self.get_stock_data(symbol)
            return "error" not in data and data.get("price", 0) > 0
        except:
            return False


# Global instance
data_aggregator = DataAggregator()
