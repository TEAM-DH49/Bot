"""
Configuration Management for Lakshya AI Trader Bot
Loads and validates all environment variables and settings
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Telegram Configuration
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    admin_ids: List[int] = Field(default=[], env="ADMIN_IDS")
    
    # Database Configuration
    database_url: str = Field(..., env="DATABASE_URL")
    database_pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_cache_ttl: int = Field(default=60, env="REDIS_CACHE_TTL")
    
    # API Keys
    alpha_vantage_api_key: Optional[str] = Field(default=None, env="ALPHA_VANTAGE_API_KEY")
    finnhub_api_key: Optional[str] = Field(default=None, env="FINNHUB_API_KEY")
    twelve_data_api_key: Optional[str] = Field(default=None, env="TWELVE_DATA_API_KEY")
    openrouter_api_key: Optional[str] = Field(default=None, env="OPENROUTER_API_KEY")
    
    # AI Configuration
    ai_model: str = Field(default="google/gemini-2.0-flash-exp:free", env="AI_MODEL")
    ai_max_tokens: int = Field(default=500, env="AI_MAX_TOKENS")
    ai_temperature: float = Field(default=0.7, env="AI_TEMPERATURE")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=20, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_day: int = Field(default=500, env="RATE_LIMIT_PER_DAY")
    max_watchlist_size: int = Field(default=50, env="MAX_WATCHLIST_SIZE")
    max_alerts: int = Field(default=100, env="MAX_ALERTS")
    
    # Market Configuration
    market_open_time: str = Field(default="09:15", env="MARKET_OPEN_TIME")
    market_close_time: str = Field(default="15:30", env="MARKET_CLOSE_TIME")
    timezone: str = Field(default="Asia/Kolkata", env="TIMEZONE")
    
    # Feature Flags
    enable_ai_analysis: bool = Field(default=True, env="ENABLE_AI_ANALYSIS")
    enable_auto_scanner: bool = Field(default=True, env="ENABLE_AUTO_SCANNER")
    enable_voice_alerts: bool = Field(default=False, env="ENABLE_VOICE_ALERTS")
    enable_daily_digest: bool = Field(default=True, env="ENABLE_DAILY_DIGEST")
    enable_pattern_recognition: bool = Field(default=True, env="ENABLE_PATTERN_RECOGNITION")
    
    # Scanner Configuration
    scanner_interval_minutes: int = Field(default=60, env="SCANNER_INTERVAL_MINUTES")
    scanner_rsi_oversold: float = Field(default=30.0, env="SCANNER_RSI_OVERSOLD")
    scanner_rsi_overbought: float = Field(default=70.0, env="SCANNER_RSI_OVERBOUGHT")
    scanner_volume_multiplier: float = Field(default=2.0, env="SCANNER_VOLUME_MULTIPLIER")
    
    # Alert Configuration
    alert_check_interval_seconds: int = Field(default=30, env="ALERT_CHECK_INTERVAL_SECONDS")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    log_file: str = Field(default="logs/lakshya_trader.log", env="LOG_FILE")
    
    # Deployment
    environment: str = Field(default="production", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    @validator("admin_ids", pre=True)
    def parse_admin_ids(cls, v):
        """Parse comma-separated admin IDs"""
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v
    
    @validator("telegram_bot_token")
    def validate_token(cls, v):
        """Validate Telegram bot token format"""
        if not v or len(v) < 20:
            raise ValueError("Invalid Telegram bot token")
        return v
    
    @validator("database_url")
    def validate_database_url(cls, v):
        """Validate database URL format"""
        if not v.startswith(("postgresql", "postgres")):
            raise ValueError("Database URL must be PostgreSQL")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in settings.admin_ids


def is_market_open() -> bool:
    """Check if market is currently open"""
    from datetime import datetime
    import pytz
    
    tz = pytz.timezone(settings.timezone)
    now = datetime.now(tz)
    
    # Check if weekend
    if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    # Parse market hours
    open_hour, open_minute = map(int, settings.market_open_time.split(":"))
    close_hour, close_minute = map(int, settings.market_close_time.split(":"))
    
    market_open = now.replace(hour=open_hour, minute=open_minute, second=0, microsecond=0)
    market_close = now.replace(hour=close_hour, minute=close_minute, second=0, microsecond=0)
    
    return market_open <= now <= market_close
