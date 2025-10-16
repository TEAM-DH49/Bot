"""
Redis Client for Caching
Handles all Redis operations for caching and rate limiting
"""
import json
import logging
from typing import Any, Optional
from datetime import timedelta

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError

from config.settings import settings
from config.constants import CACHE_TTL

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client for caching and rate limiting"""
    
    def __init__(self):
        self.client: Optional[Redis] = None
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            logger.info("Initializing Redis connection...")
            
            self.client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            
            # Test connection
            await self.client.ping()
            
            logger.info("Redis initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional TTL"""
        try:
            ttl = ttl or settings.redis_cache_ttl
            serialized = json.dumps(value, default=str)
            await self.client.setex(key, ttl, serialized)
            return True
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            await self.client.delete(key)
            return True
        except RedisError as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return await self.client.exists(key) > 0
        except RedisError as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter"""
        try:
            return await self.client.incrby(key, amount)
        except RedisError as e:
            logger.error(f"Redis INCR error for key {key}: {e}")
            return None
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key"""
        try:
            return await self.client.expire(key, seconds)
        except RedisError as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
            return False
    
    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values at once"""
        try:
            values = await self.client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value
            return result
        except RedisError as e:
            logger.error(f"Redis MGET error: {e}")
            return {}
    
    async def set_many(self, mapping: dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values at once"""
        try:
            pipeline = self.client.pipeline()
            ttl = ttl or settings.redis_cache_ttl
            
            for key, value in mapping.items():
                serialized = json.dumps(value, default=str)
                pipeline.setex(key, ttl, serialized)
            
            await pipeline.execute()
            return True
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Redis MSET error: {e}")
            return False
    
    async def get_quote_cache(self, symbol: str) -> Optional[dict]:
        """Get cached stock quote"""
        cache_key = f"quote:{symbol}"
        return await self.get(cache_key)
    
    async def set_quote_cache(self, symbol: str, data: dict) -> bool:
        """Cache stock quote"""
        cache_key = f"quote:{symbol}"
        return await self.set(cache_key, data, ttl=CACHE_TTL["QUOTE"])
    
    async def get_indicators_cache(self, symbol: str) -> Optional[dict]:
        """Get cached technical indicators"""
        cache_key = f"indicators:{symbol}"
        return await self.get(cache_key)
    
    async def set_indicators_cache(self, symbol: str, data: dict) -> bool:
        """Cache technical indicators"""
        cache_key = f"indicators:{symbol}"
        return await self.set(cache_key, data, ttl=CACHE_TTL["INDICATORS"])
    
    async def check_rate_limit(
        self,
        user_id: int,
        limit: int,
        window: int = 60
    ) -> tuple[bool, int]:
        """
        Check if user exceeded rate limit
        
        Args:
            user_id: User ID
            limit: Maximum requests allowed
            window: Time window in seconds
            
        Returns:
            (is_allowed, remaining_requests)
        """
        try:
            key = f"rate:{user_id}:{window}"
            count = await self.client.get(key)
            
            if count is None:
                # First request in window
                await self.client.setex(key, window, 1)
                return True, limit - 1
            
            count = int(count)
            
            if count >= limit:
                # Rate limit exceeded
                ttl = await self.client.ttl(key)
                return False, ttl
            
            # Increment counter
            await self.client.incr(key)
            return True, limit - count - 1
            
        except RedisError as e:
            logger.error(f"Rate limit check error: {e}")
            # Allow request on error
            return True, limit
    
    async def health_check(self) -> bool:
        """Check if Redis is healthy"""
        try:
            await self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# Global Redis client instance
redis_client = RedisClient()
