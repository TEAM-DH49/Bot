"""
RSI (Relative Strength Index) Calculator
Momentum oscillator that measures speed and change of price movements
"""
import logging
from typing import Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def calculate_rsi(prices: pd.Series, period: int = 14) -> Optional[float]:
    """
    Calculate RSI (Relative Strength Index)
    
    RSI Formula:
    RSI = 100 - (100 / (1 + RS))
    where RS = Average Gain / Average Loss
    
    Args:
        prices: Series of closing prices
        period: RSI period (default 14)
    
    Returns:
        Current RSI value (0-100) or None if insufficient data
    """
    try:
        if len(prices) < period + 1:
            logger.warning(f"Insufficient data for RSI calculation. Need {period + 1}, got {len(prices)}")
            return None
        
        # Calculate price changes
        deltas = prices.diff()
        
        # Separate gains and losses
        gains = deltas.where(deltas > 0, 0.0)
        losses = -deltas.where(deltas < 0, 0.0)
        
        # Calculate average gains and losses
        avg_gain = gains.rolling(window=period, min_periods=period).mean()
        avg_loss = losses.rolling(window=period, min_periods=period).mean()
        
        # Calculate RS (Relative Strength)
        rs = avg_gain / avg_loss
        
        # Calculate RSI
        rsi = 100 - (100 / (1 + rs))
        
        # Return the most recent RSI value
        current_rsi = rsi.iloc[-1]
        
        # Handle edge cases
        if pd.isna(current_rsi):
            return None
        if np.isinf(current_rsi):
            return 100.0  # When avg_loss is 0
        
        return round(float(current_rsi), 2)
        
    except Exception as e:
        logger.error(f"Error calculating RSI: {e}")
        return None


def calculate_rsi_series(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate RSI for entire price series
    
    Args:
        prices: Series of closing prices
        period: RSI period
    
    Returns:
        Series of RSI values
    """
    try:
        deltas = prices.diff()
        gains = deltas.where(deltas > 0, 0.0)
        losses = -deltas.where(deltas < 0, 0.0)
        
        avg_gain = gains.rolling(window=period, min_periods=period).mean()
        avg_loss = losses.rolling(window=period, min_periods=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.round(2)
        
    except Exception as e:
        logger.error(f"Error calculating RSI series: {e}")
        return pd.Series()


def get_rsi_signal(rsi: float) -> dict:
    """
    Interpret RSI value and provide signal
    
    Args:
        rsi: RSI value
    
    Returns:
        Dict with signal interpretation
    """
    if rsi is None:
        return {
            "signal": "UNKNOWN",
            "description": "Insufficient data",
            "strength": 0
        }
    
    if rsi < 20:
        return {
            "signal": "EXTREME_OVERSOLD",
            "description": "Extremely oversold - Strong bounce potential",
            "strength": 5,
            "emoji": "🔴🔴"
        }
    elif rsi < 30:
        return {
            "signal": "OVERSOLD",
            "description": "Oversold - Potential buying opportunity",
            "strength": 4,
            "emoji": "🔴"
        }
    elif rsi < 40:
        return {
            "signal": "WEAK",
            "description": "Weakening momentum",
            "strength": 2,
            "emoji": "🟡"
        }
    elif rsi <= 60:
        return {
            "signal": "NEUTRAL",
            "description": "Neutral momentum",
            "strength": 0,
            "emoji": "⚪"
        }
    elif rsi <= 70:
        return {
            "signal": "STRONG",
            "description": "Strengthening momentum",
            "strength": 2,
            "emoji": "🟢"
        }
    elif rsi <= 80:
        return {
            "signal": "OVERBOUGHT",
            "description": "Overbought - Potential selling opportunity",
            "strength": 4,
            "emoji": "🟢"
        }
    else:
        return {
            "signal": "EXTREME_OVERBOUGHT",
            "description": "Extremely overbought - Strong correction potential",
            "strength": 5,
            "emoji": "🟢🟢"
        }


def calculate_multi_timeframe_rsi(
    symbol: str,
    timeframes: dict
) -> dict:
    """
    Calculate RSI across multiple timeframes
    
    Args:
        symbol: Stock symbol
        timeframes: Dict of timeframe name to price series
    
    Returns:
        Dict of timeframe RSI values
    """
    results = {}
    
    for timeframe, prices in timeframes.items():
        rsi = calculate_rsi(prices)
        if rsi:
            results[timeframe] = {
                "rsi": rsi,
                "signal": get_rsi_signal(rsi)
            }
    
    return results


def detect_rsi_divergence(prices: pd.Series, rsi_values: pd.Series, periods: int = 14) -> Optional[dict]:
    """
    Detect bullish or bearish divergence
    
    Bullish Divergence: Price makes lower low, but RSI makes higher low
    Bearish Divergence: Price makes higher high, but RSI makes lower high
    
    Args:
        prices: Price series
        rsi_values: RSI series
        periods: Number of periods to look back
    
    Returns:
        Dict with divergence info or None
    """
    try:
        if len(prices) < periods or len(rsi_values) < periods:
            return None
        
        # Get recent data
        recent_prices = prices.iloc[-periods:]
        recent_rsi = rsi_values.iloc[-periods:]
        
        # Find price extremes
        price_min_idx = recent_prices.idxmin()
        price_max_idx = recent_prices.idxmax()
        
        # Find RSI extremes
        rsi_min_idx = recent_rsi.idxmin()
        rsi_max_idx = recent_rsi.idxmax()
        
        # Check for bullish divergence
        if price_min_idx != rsi_min_idx:
            if prices.iloc[-1] < prices.iloc[-periods//2] and rsi_values.iloc[-1] > rsi_values.iloc[-periods//2]:
                return {
                    "type": "BULLISH",
                    "description": "Bullish divergence detected - Price falling but RSI rising",
                    "strength": 4
                }
        
        # Check for bearish divergence
        if price_max_idx != rsi_max_idx:
            if prices.iloc[-1] > prices.iloc[-periods//2] and rsi_values.iloc[-1] < rsi_values.iloc[-periods//2]:
                return {
                    "type": "BEARISH",
                    "description": "Bearish divergence detected - Price rising but RSI falling",
                    "strength": 4
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Error detecting RSI divergence: {e}")
        return None
