"""
Error Handler Middleware
Handle and log errors gracefully
"""
import logging
import traceback
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseMiddleware):
    """Handle errors in bot handlers"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            # Log full traceback
            logger.error(f"Error handling message from user {event.from_user.id}")
            logger.error(f"Message: {event.text}")
            logger.error(f"Error: {e}")
            logger.error(traceback.format_exc())
            
            # Send user-friendly error message
            try:
                await event.answer(
                    "❌ <b>Oops! Something went wrong</b>\n\n"
                    "An error occurred while processing your request.\n"
                    "Please try again later or use /help for available commands.\n\n"
                    "<i>If the problem persists, please contact support.</i>"
                )
            except:
                # If we can't even send error message, just log it
                logger.error("Failed to send error message to user")
            
            # Don't re-raise - we've handled it
            return None
