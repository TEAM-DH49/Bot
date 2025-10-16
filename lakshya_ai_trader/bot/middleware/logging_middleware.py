"""
Logging Middleware
Log all user interactions for analytics
"""
import logging
from typing import Callable, Dict, Any, Awaitable
from datetime import datetime
from aiogram import BaseMiddleware
from aiogram.types import Message
from sqlalchemy import select

from database.models import User, UserActivity
from database.connection import db_manager

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Log all user interactions"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        username = event.from_user.username
        message_text = event.text or ""
        
        # Extract command
        command = message_text.split()[0] if message_text else "unknown"
        
        # Extract symbol if present
        symbol = None
        parts = message_text.split()
        if len(parts) > 1:
            symbol = parts[1].upper()
        
        # Log to console
        logger.info(
            f"User {user_id} (@{username}): {command} {symbol or ''}"
        )
        
        # Update user's last active time
        try:
            async with db_manager.session() as session:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if user:
                    user.last_active = datetime.utcnow()
                    await session.commit()
        except Exception as e:
            logger.error(f"Error updating user last active: {e}")
        
        # Call handler and measure execution time
        start_time = datetime.utcnow()
        success = True
        error_msg = None
        
        try:
            result = await handler(event, data)
        except Exception as e:
            success = False
            error_msg = str(e)
            raise
        finally:
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Log activity to database
            try:
                async with db_manager.session() as session:
                    activity = UserActivity(
                        user_id=user_id,
                        command=command,
                        symbol=symbol,
                        timestamp=start_time,
                        execution_time=execution_time,
                        success=success,
                        error_message=error_msg
                    )
                    session.add(activity)
                    await session.commit()
            except Exception as e:
                logger.error(f"Error logging user activity: {e}")
        
        return result
