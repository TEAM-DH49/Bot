"""
Rate Limiting Middleware
Prevent abuse by limiting requests per user
"""
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message

from database.redis_client import redis_client
from config.settings import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    """
    Rate limiting middleware
    
    Limits:
    - 20 requests per minute per user
    - 500 requests per day per user
    """
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        
        # Skip rate limit for admins
        if settings.is_admin(user_id):
            return await handler(event, data)
        
        # Check per-minute rate limit
        is_allowed, remaining = await redis_client.check_rate_limit(
            user_id,
            limit=settings.rate_limit_per_minute,
            window=60
        )
        
        if not is_allowed:
            await event.answer(
                f"⚠️ <b>Rate Limit Exceeded</b>\n\n"
                f"You're making requests too quickly.\n"
                f"Please wait {remaining} seconds and try again.\n\n"
                f"Limit: {settings.rate_limit_per_minute} requests per minute"
            )
            logger.warning(f"User {user_id} exceeded rate limit")
            return
        
        # Check daily rate limit
        is_allowed_daily, _ = await redis_client.check_rate_limit(
            user_id,
            limit=settings.rate_limit_per_day,
            window=86400  # 24 hours
        )
        
        if not is_allowed_daily:
            await event.answer(
                f"⚠️ <b>Daily Limit Exceeded</b>\n\n"
                f"You've reached the daily limit of {settings.rate_limit_per_day} requests.\n"
                f"Please try again tomorrow."
            )
            logger.warning(f"User {user_id} exceeded daily limit")
            return
        
        # Continue to handler
        return await handler(event, data)
