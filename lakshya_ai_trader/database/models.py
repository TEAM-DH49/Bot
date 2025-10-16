"""
Database Models for Lakshya AI Trader
All SQLAlchemy ORM models for the application
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, Enum, Index, UniqueConstraint, BigInteger
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class User(Base):
    """User model for storing Telegram user information"""
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)  # Telegram user ID
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    language = Column(String(10), default="en")
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # Settings
    enable_daily_digest = Column(Boolean, default=False)
    enable_scanner_alerts = Column(Boolean, default=False)
    enable_voice_alerts = Column(Boolean, default=False)
    
    # Relationships
    watchlist = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    portfolio = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_username", "username"),
        Index("idx_user_active", "is_active"),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Watchlist(Base):
    """User's watchlist stocks"""
    __tablename__ = "watchlist"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(50), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="watchlist")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "symbol", name="uq_user_symbol"),
        Index("idx_watchlist_user", "user_id"),
        Index("idx_watchlist_symbol", "symbol"),
    )
    
    def __repr__(self):
        return f"<Watchlist(user_id={self.user_id}, symbol={self.symbol})>"


class AlertConditionType(enum.Enum):
    """Alert condition types"""
    ABOVE = "above"
    BELOW = "below"
    RSI_ABOVE = "rsi_above"
    RSI_BELOW = "rsi_below"
    VOLUME_SPIKE = "volume_spike"
    PERCENTAGE_GAIN = "percentage_gain"
    PERCENTAGE_LOSS = "percentage_loss"


class Alert(Base):
    """Price and indicator alerts"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(50), nullable=False)
    condition_type = Column(Enum(AlertConditionType), nullable=False)
    target_value = Column(Float, nullable=False)
    current_value = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    is_triggered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    triggered_at = Column(DateTime, nullable=True)
    message = Column(Text, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="alerts")
    
    # Indexes
    __table_args__ = (
        Index("idx_alert_user", "user_id"),
        Index("idx_alert_symbol", "symbol"),
        Index("idx_alert_active", "is_active"),
    )
    
    def __repr__(self):
        return f"<Alert(user_id={self.user_id}, symbol={self.symbol}, condition={self.condition_type})>"


class Portfolio(Base):
    """User's portfolio holdings"""
    __tablename__ = "portfolio"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(50), nullable=False)
    quantity = Column(Float, nullable=False)
    buy_price = Column(Float, nullable=False)
    buy_date = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="portfolio")
    
    # Indexes
    __table_args__ = (
        Index("idx_portfolio_user", "user_id"),
        Index("idx_portfolio_symbol", "symbol"),
    )
    
    def __repr__(self):
        return f"<Portfolio(user_id={self.user_id}, symbol={self.symbol}, quantity={self.quantity})>"


class SignalType(enum.Enum):
    """Signal types from scanner"""
    RSI_OVERSOLD = "rsi_oversold"
    RSI_OVERBOUGHT = "rsi_overbought"
    MACD_BULLISH = "macd_bullish"
    MACD_BEARISH = "macd_bearish"
    VOLUME_SPIKE = "volume_spike"
    BREAKOUT = "breakout"
    BREAKDOWN = "breakdown"
    SUPPORT_BOUNCE = "support_bounce"
    RESISTANCE_REJECTION = "resistance_rejection"


class SignalLog(Base):
    """Log of all signals detected by scanner"""
    __tablename__ = "signal_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False)
    signal_type = Column(Enum(SignalType), nullable=False)
    price = Column(Float, nullable=False)
    rsi = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    volume = Column(BigInteger, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    description = Column(Text, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index("idx_signal_symbol", "symbol"),
        Index("idx_signal_type", "signal_type"),
        Index("idx_signal_timestamp", "timestamp"),
    )
    
    def __repr__(self):
        return f"<SignalLog(symbol={self.symbol}, type={self.signal_type}, timestamp={self.timestamp})>"


class MarketData(Base):
    """Cache market data for historical reference"""
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    timeframe = Column(String(10), nullable=False)  # 1m, 5m, 1h, 1d
    
    # Indexes
    __table_args__ = (
        Index("idx_market_data_symbol_time", "symbol", "timestamp"),
        Index("idx_market_data_timeframe", "timeframe"),
    )
    
    def __repr__(self):
        return f"<MarketData(symbol={self.symbol}, timestamp={self.timestamp})>"


class UserActivity(Base):
    """Track user activity for analytics"""
    __tablename__ = "user_activity"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    command = Column(String(100), nullable=False)
    symbol = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    execution_time = Column(Float, nullable=True)  # seconds
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index("idx_activity_user", "user_id"),
        Index("idx_activity_command", "command"),
        Index("idx_activity_timestamp", "timestamp"),
    )
    
    def __repr__(self):
        return f"<UserActivity(user_id={self.user_id}, command={self.command})>"


class NewsArticle(Base):
    """Store news articles for caching and sentiment analysis"""
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False)
    title = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    source = Column(String(255), nullable=True)
    published_at = Column(DateTime, nullable=False)
    sentiment_score = Column(Float, nullable=True)  # -1 to 1
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_news_symbol", "symbol"),
        Index("idx_news_published", "published_at"),
        UniqueConstraint("url", name="uq_news_url"),
    )
    
    def __repr__(self):
        return f"<NewsArticle(symbol={self.symbol}, title={self.title[:50]})>"


class BacktestResult(Base):
    """Store backtest results"""
    __tablename__ = "backtest_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(50), nullable=False)
    strategy = Column(String(100), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, default=100000.0)
    final_capital = Column(Float, nullable=False)
    total_return = Column(Float, nullable=False)
    total_trades = Column(Integer, nullable=False)
    winning_trades = Column(Integer, nullable=False)
    losing_trades = Column(Integer, nullable=False)
    win_rate = Column(Float, nullable=False)
    max_drawdown = Column(Float, nullable=False)
    sharpe_ratio = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_backtest_user", "user_id"),
        Index("idx_backtest_symbol", "symbol"),
    )
    
    def __repr__(self):
        return f"<BacktestResult(symbol={self.symbol}, strategy={self.strategy}, return={self.total_return}%)>"
