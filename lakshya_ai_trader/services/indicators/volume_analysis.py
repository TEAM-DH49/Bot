"""
Volume Analysis
Detect volume spikes, trends, and anomalies
"""
import logging
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def analyze_volume(
    volume_series: pd.Series,
    price_series: pd.Series,
    period: int = 20
) -> Dict[str, Any]:
    """
    Comprehensive volume analysis
    
    Args:
        volume_series: Volume data
        price_series: Price data
        period: Lookback period for averages
    
    Returns:
        Volume analysis results
    """
    try:
        if len(volume_series) < period:
            return {"error": "Insufficient data"}
        
        current_volume = volume_series.iloc[-1]
        avg_volume = volume_series.iloc[-period:].mean()
        
        # Calculate volume ratio
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        # Detect volume spike
        is_spike = volume_ratio > 2.0
        
        # Calculate price change
        price_change = ((price_series.iloc[-1] - price_series.iloc[-2]) / price_series.iloc[-2] * 100) if len(price_series) > 1 else 0
        
        # Determine volume-price relationship
        if is_spike and price_change > 0:
            signal = "BULLISH_VOLUME_SPIKE"
            description = "High volume with price increase - Strong buying interest"
            strength = 5
        elif is_spike and price_change < 0:
            signal = "BEARISH_VOLUME_SPIKE"
            description = "High volume with price decrease - Strong selling pressure"
            strength = 5
        elif volume_ratio < 0.5:
            signal = "LOW_VOLUME"
            description = "Below average volume - Lack of conviction"
            strength = 2
        elif volume_ratio > 1.5:
            signal = "HIGH_VOLUME"
            description = "Above average volume - Increased interest"
            strength = 3
        else:
            signal = "NORMAL_VOLUME"
            description = "Normal volume levels"
            strength = 0
        
        return {
            "current_volume": int(current_volume),
            "average_volume": int(avg_volume),
            "volume_ratio": round(float(volume_ratio), 2),
            "is_spike": is_spike,
            "signal": signal,
            "description": description,
            "strength": strength,
            "price_change_pct": round(float(price_change), 2)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing volume: {e}")
        return {"error": str(e)}


def calculate_obv(prices: pd.Series, volume: pd.Series) -> Optional[pd.Series]:
    """
    Calculate On-Balance Volume (OBV)
    
    OBV adds volume on up days and subtracts volume on down days
    
    Args:
        prices: Price series
        volume: Volume series
    
    Returns:
        OBV series
    """
    try:
        if len(prices) != len(volume):
            return None
        
        price_change = prices.diff()
        
        obv = pd.Series(index=prices.index, dtype=float)
        obv.iloc[0] = volume.iloc[0]
        
        for i in range(1, len(prices)):
            if price_change.iloc[i] > 0:
                obv.iloc[i] = obv.iloc[i - 1] + volume.iloc[i]
            elif price_change.iloc[i] < 0:
                obv.iloc[i] = obv.iloc[i - 1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i - 1]
        
        return obv
        
    except Exception as e:
        logger.error(f"Error calculating OBV: {e}")
        return None


def detect_volume_divergence(
    prices: pd.Series,
    volume: pd.Series,
    periods: int = 20
) -> Optional[Dict[str, Any]]:
    """
    Detect price-volume divergence
    
    Divergence occurs when price and volume move in opposite directions
    
    Args:
        prices: Price series
        volume: Volume series
        periods: Lookback period
    
    Returns:
        Divergence info or None
    """
    try:
        if len(prices) < periods or len(volume) < periods:
            return None
        
        recent_prices = prices.iloc[-periods:]
        recent_volume = volume.iloc[-periods:]
        
        # Calculate trends
        price_trend = np.polyfit(range(len(recent_prices)), recent_prices, 1)[0]
        volume_trend = np.polyfit(range(len(recent_volume)), recent_volume, 1)[0]
        
        # Bullish divergence: Price falling but volume increasing
        if price_trend < 0 and volume_trend > 0:
            return {
                "type": "BULLISH_DIVERGENCE",
                "description": "Price declining with increasing volume - Potential reversal",
                "strength": 4
            }
        
        # Bearish divergence: Price rising but volume decreasing
        if price_trend > 0 and volume_trend < 0:
            return {
                "type": "BEARISH_DIVERGENCE",
                "description": "Price rising with decreasing volume - Weak rally",
                "strength": 4
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error detecting volume divergence: {e}")
        return None


def calculate_vwap(prices: pd.Series, volume: pd.Series, high: pd.Series, low: pd.Series) -> Optional[float]:
    """
    Calculate Volume Weighted Average Price (VWAP)
    
    VWAP = Σ(Price × Volume) / Σ(Volume)
    where Price = (High + Low + Close) / 3
    
    Args:
        prices: Close prices
        volume: Volume data
        high: High prices
        low: Low prices
    
    Returns:
        Current VWAP value
    """
    try:
        typical_price = (high + low + prices) / 3
        vwap = (typical_price * volume).sum() / volume.sum()
        
        return round(float(vwap), 2)
        
    except Exception as e:
        logger.error(f"Error calculating VWAP: {e}")
        return None


def get_vwap_signal(current_price: float, vwap: float) -> Dict[str, Any]:
    """
    Interpret price position relative to VWAP
    
    Args:
        current_price: Current market price
        vwap: VWAP value
    
    Returns:
        VWAP signal interpretation
    """
    try:
        diff_pct = ((current_price - vwap) / vwap) * 100
        
        if current_price > vwap * 1.02:
            return {
                "signal": "ABOVE_VWAP",
                "description": f"Price {abs(diff_pct):.2f}% above VWAP - Bullish",
                "emoji": "🟢",
                "strength": 3
            }
        elif current_price < vwap * 0.98:
            return {
                "signal": "BELOW_VWAP",
                "description": f"Price {abs(diff_pct):.2f}% below VWAP - Bearish",
                "emoji": "🔴",
                "strength": 3
            }
        else:
            return {
                "signal": "NEAR_VWAP",
                "description": "Price near VWAP - Neutral",
                "emoji": "⚪",
                "strength": 0
            }
        
    except Exception as e:
        logger.error(f"Error getting VWAP signal: {e}")
        return {}
