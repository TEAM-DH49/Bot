"""
OpenRouter AI Client
Connect to OpenRouter API for AI-powered insights
"""
import logging
from typing import Optional, Dict, Any, List
import aiohttp
import json

from config.settings import settings

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Client for OpenRouter API (free AI models)"""
    
    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.model = settings.ai_model
        self.max_tokens = settings.ai_max_tokens
        self.temperature = settings.ai_temperature
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def chat_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Optional[str]:
        """
        Send chat completion request
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            max_tokens: Maximum tokens in response
            temperature: Randomness (0-1)
        
        Returns:
            AI response text or None
        """
        if not self.api_key:
            logger.error("OpenRouter API key not configured")
            return None
        
        try:
            await self._ensure_session()
            
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/lakshya-ai-trader",
                "X-Title": "Lakshya AI Trader Bot"
            }
            
            logger.info(f"Sending AI request with model: {self.model}")
            
            async with self.session.post(
                self.BASE_URL,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"OpenRouter API error {response.status}: {error_text}")
                    return None
                
                data = await response.json()
                
                # Extract response text
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    logger.info("AI response received successfully")
                    return content.strip()
                
                logger.error("No choices in AI response")
                return None
                
        except asyncio.TimeoutError:
            logger.error("AI request timed out")
            return None
        except Exception as e:
            logger.error(f"Error in AI chat completion: {e}")
            return None
    
    async def analyze_stock(
        self,
        symbol: str,
        data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Analyze stock with AI
        
        Args:
            symbol: Stock symbol
            data: Stock data including price, indicators, news
        
        Returns:
            AI analysis text
        """
        try:
            from services.ai.prompts import build_stock_analysis_prompt
            
            prompt = build_stock_analysis_prompt(symbol, data)
            
            system_prompt = """You are an expert Indian stock market analyst. 
Provide clear, educational analysis in simple Hindi-English mix. 
Explain technical indicators and what they mean for traders.
NEVER give buy/sell recommendations. Only explain what the data suggests.
Keep responses concise (3-4 sentences max)."""
            
            response = await self.chat_completion(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=500
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in stock analysis: {e}")
            return None
    
    async def explain_signal(
        self,
        symbol: str,
        signal_type: str,
        details: str
    ) -> Optional[str]:
        """
        Explain a trading signal in simple terms
        
        Args:
            symbol: Stock symbol
            signal_type: Type of signal (RSI, MACD, etc.)
            details: Signal details
        
        Returns:
            Explanation text
        """
        try:
            prompt = f"""
Stock: {symbol}
Signal Type: {signal_type}
Details: {details}

Explain this signal in 2-3 simple sentences that a beginner can understand.
Use Hindi-English mix. What does this mean for the stock?
"""
            
            system_prompt = "You are explaining stock signals to beginners. Be clear and educational."
            
            response = await self.chat_completion(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=200
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error explaining signal: {e}")
            return None
    
    async def summarize_news(
        self,
        symbol: str,
        headlines: List[str]
    ) -> Optional[str]:
        """
        Summarize multiple news headlines
        
        Args:
            symbol: Stock symbol
            headlines: List of news headlines
        
        Returns:
            Summary text
        """
        try:
            headlines_text = "\n".join(f"{i+1}. {h}" for i, h in enumerate(headlines[:5]))
            
            prompt = f"""
Stock: {symbol}
Recent News Headlines:
{headlines_text}

Summarize the overall news sentiment for {symbol} in 2-3 sentences.
Is the news positive, negative, or neutral? What's the key theme?
"""
            
            system_prompt = "Summarize stock news sentiment objectively."
            
            response = await self.chat_completion(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=200
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error summarizing news: {e}")
            return None
    
    async def answer_question(
        self,
        question: str,
        context: Optional[str] = None
    ) -> Optional[str]:
        """
        Answer user's stock market question
        
        Args:
            question: User's question
            context: Optional context (stock data, etc.)
        
        Returns:
            Answer text
        """
        try:
            if context:
                prompt = f"Context:\n{context}\n\nQuestion: {question}"
            else:
                prompt = question
            
            system_prompt = """You are an Indian stock market expert assistant.
Answer questions clearly in Hindi-English mix.
Always add disclaimer: This is educational information, not financial advice.
If you don't know something, say so."""
            
            response = await self.chat_completion(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=500
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return None


# Global instance
ai_client = OpenRouterClient()


# Add missing import
import asyncio
