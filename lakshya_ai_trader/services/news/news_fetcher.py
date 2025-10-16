"""
News Fetcher
Fetch stock news from multiple sources
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import aiohttp
import feedparser
from bs4 import BeautifulSoup

from services.data.finnhub_client import finnhub_client
from database.redis_client import redis_client

logger = logging.getLogger(__name__)


class NewsFetcher:
    """Fetch news from multiple sources"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def fetch_google_news(self, symbol: str, company_name: str = None) -> List[Dict[str, Any]]:
        """
        Fetch news from Google News RSS
        
        Args:
            symbol: Stock symbol
            company_name: Company name for better search
        
        Returns:
            List of news articles
        """
        try:
            # Use company name if provided, otherwise symbol
            query = company_name if company_name else symbol
            
            rss_url = f"https://news.google.com/rss/search?q={query}+stock+India&hl=en-IN&gl=IN&ceid=IN:en"
            
            # Parse RSS feed
            feed = feedparser.parse(rss_url)
            
            articles = []
            for entry in feed.entries[:10]:  # Limit to 10 articles
                articles.append({
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "published_at": entry.get("published", ""),
                    "source": "Google News",
                    "summary": entry.get("summary", "")
                })
            
            logger.info(f"Fetched {len(articles)} articles from Google News for {symbol}")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching Google News for {symbol}: {e}")
            return []
    
    async def fetch_finnhub_news(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch news from Finnhub"""
        try:
            news = await finnhub_client.get_company_news(symbol, days=7)
            
            logger.info(f"Fetched {len(news)} articles from Finnhub for {symbol}")
            return news
            
        except Exception as e:
            logger.error(f"Error fetching Finnhub news for {symbol}: {e}")
            return []
    
    async def fetch_moneycontrol_news(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Scrape news from MoneyControl (if feasible)
        
        Note: Web scraping should respect robots.txt and rate limits
        """
        try:
            await self._ensure_session()
            
            # MoneyControl news URL format
            url = f"https://www.moneycontrol.com/news/tags/{symbol.lower()}.html"
            
            async with self.session.get(url, timeout=10) as response:
                if response.status != 200:
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find news articles (this is a simplified example)
                articles = []
                news_items = soup.find_all('li', class_='clearfix', limit=5)
                
                for item in news_items:
                    title_tag = item.find('h2')
                    link_tag = item.find('a')
                    
                    if title_tag and link_tag:
                        articles.append({
                            "title": title_tag.get_text(strip=True),
                            "url": link_tag.get('href', ''),
                            "source": "MoneyControl",
                            "published_at": datetime.now().isoformat()
                        })
                
                return articles
                
        except Exception as e:
            logger.error(f"Error scraping MoneyControl news: {e}")
            return []
    
    async def get_all_news(
        self,
        symbol: str,
        company_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Aggregate news from all sources
        
        Args:
            symbol: Stock symbol
            company_name: Optional company name
        
        Returns:
            Combined list of news articles
        """
        # Check cache first
        cache_key = f"news:{symbol}"
        cached = await redis_client.get(cache_key)
        if cached:
            logger.info(f"Returning cached news for {symbol}")
            return cached
        
        # Fetch from all sources
        google_news = await self.fetch_google_news(symbol, company_name)
        finnhub_news = await self.fetch_finnhub_news(symbol)
        
        # Combine and deduplicate
        all_news = google_news + finnhub_news
        
        # Remove duplicates based on title similarity
        unique_news = []
        seen_titles = set()
        
        for article in all_news:
            title_lower = article.get("title", "").lower()
            if title_lower and title_lower not in seen_titles:
                unique_news.append(article)
                seen_titles.add(title_lower)
        
        # Sort by published date (most recent first)
        unique_news.sort(
            key=lambda x: x.get("published_at", ""),
            reverse=True
        )
        
        # Limit to 15 articles
        result = unique_news[:15]
        
        # Cache for 30 minutes
        await redis_client.set(cache_key, result, ttl=1800)
        
        logger.info(f"Fetched total {len(result)} unique news articles for {symbol}")
        return result
    
    async def get_market_news(self) -> List[Dict[str, Any]]:
        """Get general Indian market news"""
        try:
            # Finnhub general news
            finnhub_news = await finnhub_client.get_market_news("general")
            
            # Google News for Indian markets
            rss_url = "https://news.google.com/rss/search?q=Indian+stock+market+today&hl=en-IN&gl=IN&ceid=IN:en"
            feed = feedparser.parse(rss_url)
            
            google_news = []
            for entry in feed.entries[:10]:
                google_news.append({
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "published_at": entry.get("published", ""),
                    "source": "Google News"
                })
            
            # Combine
            all_news = finnhub_news + google_news
            
            return all_news[:20]
            
        except Exception as e:
            logger.error(f"Error fetching market news: {e}")
            return []


# Global instance
news_fetcher = NewsFetcher()
