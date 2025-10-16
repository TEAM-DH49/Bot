"""
Finnhub API Client
For real-time quotes and news data
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import finnhub

from config.settings import settings

logger = logging.getLogger(__name__)


class FinnhubClient:
    """Client for Finnhub API"""
    
    def __init__(self):
        self.api_key = settings.finnhub_api_key
        self.client = None
        if self.api_key:
            self.client = finnhub.Client(api_key=self.api_key)
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Convert to Finnhub format"""
        symbol = symbol.upper().strip()
        
        # Finnhub uses NSE: prefix for Indian stocks
        if not symbol.startswith("NSE:"):
            symbol = f"NSE:{symbol}"
        
        return symbol
    
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote"""
        if not self.client:
            return {"error": "Finnhub API key not configured"}
        
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            
            quote = self.client.quote(normalized_symbol)
            
            if not quote or quote.get("c", 0) == 0:
                return {"error": "No data found"}
            
            current_price = quote.get("c", 0)  # Current price
            previous_close = quote.get("pc", 0)  # Previous close
            change = current_price - previous_close
            change_pct = (change / previous_close * 100) if previous_close else 0
            
            return {
                "symbol": symbol,
                "normalized_symbol": normalized_symbol,
                "price": round(current_price, 2),
                "previous_close": round(previous_close, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "high": round(quote.get("h", 0), 2),  # High price of the day
                "low": round(quote.get("l", 0), 2),  # Low price of the day
                "open": round(quote.get("o", 0), 2),  # Open price of the day
                "timestamp": datetime.fromtimestamp(quote.get("t", 0)).isoformat(),
                "source": "finnhub"
            }
            
        except Exception as e:
            logger.error(f"Finnhub quote error for {symbol}: {e}")
            return {"error": str(e)}
    
    async def get_company_news(
        self,
        symbol: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get company news
        
        Args:
            symbol: Stock symbol
            days: Number of days to look back
        
        Returns:
            List of news articles
        """
        if not self.client:
            return []
        
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            news = self.client.company_news(
                normalized_symbol,
                _from=start_date.strftime("%Y-%m-%d"),
                to=end_date.strftime("%Y-%m-%d")
            )
            
            if not news:
                return []
            
            # Format news items
            formatted_news = []
            for item in news[:10]:  # Limit to 10 articles
                formatted_news.append({
                    "title": item.get("headline"),
                    "summary": item.get("summary"),
                    "url": item.get("url"),
                    "source": item.get("source"),
                    "published_at": datetime.fromtimestamp(item.get("datetime", 0)).isoformat(),
                    "image": item.get("image"),
                })
            
            return formatted_news
            
        except Exception as e:
            logger.error(f"Finnhub news error for {symbol}: {e}")
            return []
    
    async def get_market_news(self, category: str = "general") -> List[Dict[str, Any]]:
        """
        Get general market news
        
        Args:
            category: News category (general, forex, crypto, merger)
        """
        if not self.client:
            return []
        
        try:
            news = self.client.general_news(category, minid=0)
            
            if not news:
                return []
            
            formatted_news = []
            for item in news[:10]:
                formatted_news.append({
                    "title": item.get("headline"),
                    "summary": item.get("summary"),
                    "url": item.get("url"),
                    "source": item.get("source"),
                    "published_at": datetime.fromtimestamp(item.get("datetime", 0)).isoformat(),
                })
            
            return formatted_news
            
        except Exception as e:
            logger.error(f"Finnhub market news error: {e}")
            return []
    
    async def get_recommendation(self, symbol: str) -> Dict[str, Any]:
        """Get analyst recommendations"""
        if not self.client:
            return {}
        
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            recommendations = self.client.recommendation_trends(normalized_symbol)
            
            if not recommendations:
                return {}
            
            # Get latest recommendation
            latest = recommendations[0]
            
            return {
                "period": latest.get("period"),
                "strong_buy": latest.get("strongBuy", 0),
                "buy": latest.get("buy", 0),
                "hold": latest.get("hold", 0),
                "sell": latest.get("sell", 0),
                "strong_sell": latest.get("strongSell", 0),
            }
            
        except Exception as e:
            logger.error(f"Finnhub recommendation error for {symbol}: {e}")
            return {}


# Global instance
finnhub_client = FinnhubClient()
