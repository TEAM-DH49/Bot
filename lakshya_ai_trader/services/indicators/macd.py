"""
MACD (Moving Average Convergence Divergence) Calculator
Shows relationship between two moving averages
"""
import logging
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average
    
    Args:
        prices: Price series
        period: EMA period
    
    Returns:
        EMA series
    """
    return prices.ewm(span=period, adjust=False).mean()


def calculate_macd(
    prices: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Optional[Dict[str, Any]]:
    """
    Calculate MACD indicator
    
    MACD Line = 12-EMA - 26-EMA
    Signal Line = 9-EMA of MACD Line
    Histogram = MACD Line - Signal Line
    
    Args:
        prices: Series of closing prices
        fast_period: Fast EMA period (default 12)
        slow_period: Slow EMA period (default 26)
        signal_period: Signal line EMA period (default 9)
    
    Returns:
        Dict with MACD values and signal
    """
    try:
        if len(prices) < slow_period + signal_period:
            logger.warning(f"Insufficient data for MACD calculation")
            return None
        
        # Calculate EMAs
        ema_fast = calculate_ema(prices, fast_period)
        ema_slow = calculate_ema(prices, slow_period)
        
        # Calculate MACD line
        macd_line = ema_fast - ema_slow
        
        # Calculate Signal line
        signal_line = calculate_ema(macd_line, signal_period)
        
        # Calculate Histogram
        histogram = macd_line - signal_line
        
        # Get current values
        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        current_histogram = histogram.iloc[-1]
        
        # Get previous values for crossover detection
        prev_macd = macd_line.iloc[-2] if len(macd_line) > 1 else current_macd
        prev_signal = signal_line.iloc[-2] if len(signal_line) > 1 else current_signal
        
        # Determine signal type
        if current_macd > current_signal:
            signal_type = "BULLISH"
        elif current_macd < current_signal:
            signal_type = "BEARISH"
        else:
            signal_type = "NEUTRAL"
        
        # Detect crossovers
        crossover = None
        if prev_macd <= prev_signal and current_macd > current_signal:
            crossover = "BULLISH_CROSSOVER"
        elif prev_macd >= prev_signal and current_macd < current_signal:
            crossover = "BEARISH_CROSSOVER"
        
        return {
            "macd_line": round(float(current_macd), 2),
            "signal_line": round(float(current_signal), 2),
            "histogram": round(float(current_histogram), 2),
            "signal_type": signal_type,
            "crossover": crossover,
            "strength": abs(float(current_histogram))
        }
        
    except Exception as e:
        logger.error(f"Error calculating MACD: {e}")
        return None


def calculate_macd_series(
    prices: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Dict[str, pd.Series]:
    """
    Calculate MACD for entire series
    
    Returns:
        Dict with macd_line, signal_line, and histogram series
    """
    try:
        ema_fast = calculate_ema(prices, fast_period)
        ema_slow = calculate_ema(prices, slow_period)
        
        macd_line = ema_fast - ema_slow
        signal_line = calculate_ema(macd_line, signal_period)
        histogram = macd_line - signal_line
        
        return {
            "macd_line": macd_line.round(2),
            "signal_line": signal_line.round(2),
            "histogram": histogram.round(2)
        }
        
    except Exception as e:
        logger.error(f"Error calculating MACD series: {e}")
        return {}


def get_macd_signal(macd_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interpret MACD and provide trading signal
    
    Args:
        macd_data: MACD calculation results
    
    Returns:
        Dict with interpretation
    """
    if not macd_data:
        return {
            "signal": "UNKNOWN",
            "description": "Insufficient data",
            "emoji": "⚪"
        }
    
    signal_type = macd_data.get("signal_type")
    crossover = macd_data.get("crossover")
    histogram = macd_data.get("histogram", 0)
    
    if crossover == "BULLISH_CROSSOVER":
        return {
            "signal": "STRONG_BUY",
            "description": "🚀 Bullish crossover - MACD crossed above signal line",
            "emoji": "🟢🟢",
            "strength": 5
        }
    elif crossover == "BEARISH_CROSSOVER":
        return {
            "signal": "STRONG_SELL",
            "description": "⚠️ Bearish crossover - MACD crossed below signal line",
            "emoji": "🔴🔴",
            "strength": 5
        }
    elif signal_type == "BULLISH":
        if histogram > 0.5:
            return {
                "signal": "BUY",
                "description": "Bullish momentum - MACD above signal line",
                "emoji": "🟢",
                "strength": 3
            }
        else:
            return {
                "signal": "WEAK_BUY",
                "description": "Weakly bullish - MACD slightly above signal",
                "emoji": "🟡",
                "strength": 2
            }
    elif signal_type == "BEARISH":
        if histogram < -0.5:
            return {
                "signal": "SELL",
                "description": "Bearish momentum - MACD below signal line",
                "emoji": "🔴",
                "strength": 3
            }
        else:
            return {
                "signal": "WEAK_SELL",
                "description": "Weakly bearish - MACD slightly below signal",
                "emoji": "🟡",
                "strength": 2
            }
    else:
        return {
            "signal": "NEUTRAL",
            "description": "Neutral - MACD near signal line",
            "emoji": "⚪",
            "strength": 0
        }


def detect_macd_divergence(prices: pd.Series, macd_series: pd.Series, periods: int = 20) -> Optional[Dict[str, Any]]:
    """
    Detect MACD divergence patterns
    
    Args:
        prices: Price series
        macd_series: MACD histogram series
        periods: Lookback period
    
    Returns:
        Divergence information or None
    """
    try:
        if len(prices) < periods or len(macd_series) < periods:
            return None
        
        recent_prices = prices.iloc[-periods:]
        recent_macd = macd_series.iloc[-periods:]
        
        # Find extremes
        price_lows = recent_prices.nsmallest(2)
        price_highs = recent_prices.nlargest(2)
        macd_lows = recent_macd.nsmallest(2)
        macd_highs = recent_macd.nlargest(2)
        
        # Bullish divergence: price making lower lows, MACD making higher lows
        if len(price_lows) >= 2 and len(macd_lows) >= 2:
            if price_lows.iloc[-1] < price_lows.iloc[0] and macd_lows.iloc[-1] > macd_lows.iloc[0]:
                return {
                    "type": "BULLISH_DIVERGENCE",
                    "description": "Bullish divergence - Potential trend reversal",
                    "strength": 4
                }
        
        # Bearish divergence: price making higher highs, MACD making lower highs
        if len(price_highs) >= 2 and len(macd_highs) >= 2:
            if price_highs.iloc[-1] > price_highs.iloc[0] and macd_highs.iloc[-1] < macd_highs.iloc[0]:
                return {
                    "type": "BEARISH_DIVERGENCE",
                    "description": "Bearish divergence - Potential trend reversal",
                    "strength": 4
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Error detecting MACD divergence: {e}")
        return None
