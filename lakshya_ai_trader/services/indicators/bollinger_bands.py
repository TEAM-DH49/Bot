"""
Bollinger Bands Calculator
Volatility bands placed above and below a moving average
"""
import logging
from typing import Optional, Dict, Any
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_bollinger_bands(
    prices: pd.Series,
    period: int = 20,
    std_dev: float = 2.0
) -> Optional[Dict[str, Any]]:
    """
    Calculate Bollinger Bands
    
    Middle Band = 20-period Simple Moving Average
    Upper Band = Middle Band + (2 × Standard Deviation)
    Lower Band = Middle Band - (2 × Standard Deviation)
    
    Args:
        prices: Series of closing prices
        period: Moving average period (default 20)
        std_dev: Number of standard deviations (default 2.0)
    
    Returns:
        Dict with band values and signal
    """
    try:
        if len(prices) < period:
            logger.warning(f"Insufficient data for Bollinger Bands")
            return None
        
        # Calculate middle band (SMA)
        middle_band = prices.rolling(window=period).mean()
        
        # Calculate standard deviation
        rolling_std = prices.rolling(window=period).std()
        
        # Calculate upper and lower bands
        upper_band = middle_band + (rolling_std * std_dev)
        lower_band = middle_band - (rolling_std * std_dev)
        
        # Get current values
        current_price = prices.iloc[-1]
        current_upper = upper_band.iloc[-1]
        current_middle = middle_band.iloc[-1]
        current_lower = lower_band.iloc[-1]
        
        # Calculate bandwidth (volatility measure)
        bandwidth = ((current_upper - current_lower) / current_middle) * 100
        
        # Calculate %B (price position within bands)
        percent_b = (current_price - current_lower) / (current_upper - current_lower)
        
        # Determine signal
        if current_price >= current_upper:
            signal = "OVERBOUGHT"
            description = "Price at or above upper band - Potentially overbought"
        elif current_price <= current_lower:
            signal = "OVERSOLD"
            description = "Price at or below lower band - Potentially oversold"
        elif current_price > current_middle:
            signal = "BULLISH"
            description = "Price above middle band - Bullish territory"
        elif current_price < current_middle:
            signal = "BEARISH"
            description = "Price below middle band - Bearish territory"
        else:
            signal = "NEUTRAL"
            description = "Price near middle band"
        
        return {
            "upper_band": round(float(current_upper), 2),
            "middle_band": round(float(current_middle), 2),
            "lower_band": round(float(current_lower), 2),
            "current_price": round(float(current_price), 2),
            "bandwidth": round(float(bandwidth), 2),
            "percent_b": round(float(percent_b), 2),
            "signal": signal,
            "description": description
        }
        
    except Exception as e:
        logger.error(f"Error calculating Bollinger Bands: {e}")
        return None


def calculate_bollinger_bands_series(
    prices: pd.Series,
    period: int = 20,
    std_dev: float = 2.0
) -> Dict[str, pd.Series]:
    """
    Calculate Bollinger Bands for entire series
    
    Returns:
        Dict with upper, middle, and lower band series
    """
    try:
        middle_band = prices.rolling(window=period).mean()
        rolling_std = prices.rolling(window=period).std()
        
        upper_band = middle_band + (rolling_std * std_dev)
        lower_band = middle_band - (rolling_std * std_dev)
        
        return {
            "upper": upper_band.round(2),
            "middle": middle_band.round(2),
            "lower": lower_band.round(2)
        }
        
    except Exception as e:
        logger.error(f"Error calculating Bollinger Bands series: {e}")
        return {}


def detect_squeeze(prices: pd.Series, period: int = 20) -> Optional[Dict[str, Any]]:
    """
    Detect Bollinger Band squeeze (low volatility)
    
    Squeeze occurs when bandwidth is historically low,
    often preceding significant price moves
    
    Args:
        prices: Price series
        period: BB period
    
    Returns:
        Squeeze information or None
    """
    try:
        if len(prices) < period * 2:
            return None
        
        # Calculate bands
        middle_band = prices.rolling(window=period).mean()
        rolling_std = prices.rolling(window=period).std()
        upper_band = middle_band + (rolling_std * 2)
        lower_band = middle_band - (rolling_std * 2)
        
        # Calculate bandwidth
        bandwidth = ((upper_band - lower_band) / middle_band) * 100
        
        # Get current and historical bandwidth
        current_bw = bandwidth.iloc[-1]
        avg_bw = bandwidth.iloc[-period:].mean()
        min_bw = bandwidth.iloc[-period:].min()
        
        # Check if in squeeze (current bandwidth near historical low)
        if current_bw <= min_bw * 1.1:  # Within 10% of minimum
            return {
                "type": "SQUEEZE",
                "description": "Bollinger Band squeeze detected - Low volatility, breakout expected",
                "current_bandwidth": round(float(current_bw), 2),
                "average_bandwidth": round(float(avg_bw), 2),
                "strength": 4
            }
        
        # Check for expansion (high volatility)
        max_bw = bandwidth.iloc[-period:].max()
        if current_bw >= max_bw * 0.9:
            return {
                "type": "EXPANSION",
                "description": "Bollinger Band expansion - High volatility ongoing",
                "current_bandwidth": round(float(current_bw), 2),
                "average_bandwidth": round(float(avg_bw), 2),
                "strength": 3
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error detecting squeeze: {e}")
        return None


def detect_band_walk(prices: pd.Series, period: int = 20, consecutive: int = 5) -> Optional[str]:
    """
    Detect when price walks along upper or lower band
    
    Band walk indicates strong trend continuation
    
    Args:
        prices: Price series
        period: BB period
        consecutive: Number of consecutive touches required
    
    Returns:
        "UPPER_WALK", "LOWER_WALK", or None
    """
    try:
        if len(prices) < period + consecutive:
            return None
        
        # Calculate bands
        middle_band = prices.rolling(window=period).mean()
        rolling_std = prices.rolling(window=period).std()
        upper_band = middle_band + (rolling_std * 2)
        lower_band = middle_band - (rolling_std * 2)
        
        # Get recent prices and bands
        recent_prices = prices.iloc[-consecutive:]
        recent_upper = upper_band.iloc[-consecutive:]
        recent_lower = lower_band.iloc[-consecutive:]
        
        # Check for upper band walk
        upper_touches = sum(recent_prices >= recent_upper * 0.98)  # Within 2% of upper band
        if upper_touches >= consecutive - 1:
            return "UPPER_WALK"
        
        # Check for lower band walk
        lower_touches = sum(recent_prices <= recent_lower * 1.02)  # Within 2% of lower band
        if lower_touches >= consecutive - 1:
            return "LOWER_WALK"
        
        return None
        
    except Exception as e:
        logger.error(f"Error detecting band walk: {e}")
        return None
