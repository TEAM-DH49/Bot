"""
Pivot Points Calculator
Support and resistance levels for intraday trading
"""
import logging
from typing import Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_pivot_points(high: float, low: float, close: float) -> Dict[str, float]:
    """
    Calculate standard pivot points
    
    Pivot Point (PP) = (High + Low + Close) / 3
    
    Resistance levels:
    R1 = (2 × PP) - Low
    R2 = PP + (High - Low)
    R3 = High + 2(PP - Low)
    
    Support levels:
    S1 = (2 × PP) - High
    S2 = PP - (High - Low)
    S3 = Low - 2(High - PP)
    
    Args:
        high: Previous period high
        low: Previous period low
        close: Previous period close
    
    Returns:
        Dict with pivot point and support/resistance levels
    """
    try:
        # Calculate pivot point
        pivot = (high + low + close) / 3
        
        # Calculate resistance levels
        r1 = (2 * pivot) - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)
        
        # Calculate support levels
        s1 = (2 * pivot) - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)
        
        return {
            "pivot": round(pivot, 2),
            "r1": round(r1, 2),
            "r2": round(r2, 2),
            "r3": round(r3, 2),
            "s1": round(s1, 2),
            "s2": round(s2, 2),
            "s3": round(s3, 2),
        }
        
    except Exception as e:
        logger.error(f"Error calculating pivot points: {e}")
        return {}


def calculate_fibonacci_pivots(high: float, low: float, close: float) -> Dict[str, float]:
    """
    Calculate Fibonacci pivot points
    
    Uses Fibonacci ratios: 0.382, 0.618, 1.000
    """
    try:
        pivot = (high + low + close) / 3
        range_val = high - low
        
        r1 = pivot + (0.382 * range_val)
        r2 = pivot + (0.618 * range_val)
        r3 = pivot + (1.000 * range_val)
        
        s1 = pivot - (0.382 * range_val)
        s2 = pivot - (0.618 * range_val)
        s3 = pivot - (1.000 * range_val)
        
        return {
            "pivot": round(pivot, 2),
            "r1": round(r1, 2),
            "r2": round(r2, 2),
            "r3": round(r3, 2),
            "s1": round(s1, 2),
            "s2": round(s2, 2),
            "s3": round(s3, 2),
        }
        
    except Exception as e:
        logger.error(f"Error calculating Fibonacci pivots: {e}")
        return {}


def calculate_camarilla_pivots(high: float, low: float, close: float) -> Dict[str, float]:
    """
    Calculate Camarilla pivot points
    
    More sensitive to price action, good for range-bound markets
    """
    try:
        range_val = high - low
        
        # Camarilla formula
        r1 = close + (range_val * 1.1 / 12)
        r2 = close + (range_val * 1.1 / 6)
        r3 = close + (range_val * 1.1 / 4)
        r4 = close + (range_val * 1.1 / 2)
        
        s1 = close - (range_val * 1.1 / 12)
        s2 = close - (range_val * 1.1 / 6)
        s3 = close - (range_val * 1.1 / 4)
        s4 = close - (range_val * 1.1 / 2)
        
        return {
            "r1": round(r1, 2),
            "r2": round(r2, 2),
            "r3": round(r3, 2),
            "r4": round(r4, 2),
            "s1": round(s1, 2),
            "s2": round(s2, 2),
            "s3": round(s3, 2),
            "s4": round(s4, 2),
        }
        
    except Exception as e:
        logger.error(f"Error calculating Camarilla pivots: {e}")
        return {}


def get_pivot_analysis(current_price: float, pivots: Dict[str, float]) -> Dict[str, Any]:
    """
    Analyze current price position relative to pivot points
    
    Args:
        current_price: Current market price
        pivots: Pivot points dict
    
    Returns:
        Analysis with nearest support/resistance
    """
    try:
        pivot = pivots.get("pivot", 0)
        
        # Identify nearest support and resistance
        supports = [(k, v) for k, v in pivots.items() if k.startswith("s") and v < current_price]
        resistances = [(k, v) for k, v in pivots.items() if k.startswith("r") and v > current_price]
        
        nearest_support = max(supports, key=lambda x: x[1]) if supports else None
        nearest_resistance = min(resistances, key=lambda x: x[1]) if resistances else None
        
        # Determine bias
        if current_price > pivot:
            bias = "BULLISH"
            description = f"Price above pivot (₹{pivot}) - Bullish bias"
        elif current_price < pivot:
            bias = "BEARISH"
            description = f"Price below pivot (₹{pivot}) - Bearish bias"
        else:
            bias = "NEUTRAL"
            description = "Price at pivot point"
        
        return {
            "bias": bias,
            "description": description,
            "pivot_point": pivot,
            "current_price": current_price,
            "nearest_support": {
                "level": nearest_support[0],
                "price": nearest_support[1]
            } if nearest_support else None,
            "nearest_resistance": {
                "level": nearest_resistance[0],
                "price": nearest_resistance[1]
            } if nearest_resistance else None,
        }
        
    except Exception as e:
        logger.error(f"Error in pivot analysis: {e}")
        return {}


def detect_pivot_breakout(price_series: pd.Series, pivots: Dict[str, float]) -> Optional[Dict[str, Any]]:
    """
    Detect if price broke through significant pivot level
    
    Args:
        price_series: Recent price data
        pivots: Pivot points
    
    Returns:
        Breakout information or None
    """
    try:
        if len(price_series) < 2:
            return None
        
        current_price = price_series.iloc[-1]
        previous_price = price_series.iloc[-2]
        
        # Check R1, R2, R3 breakouts
        for level in ["r1", "r2", "r3"]:
            resistance = pivots.get(level, 0)
            if previous_price < resistance <= current_price:
                return {
                    "type": "RESISTANCE_BREAKOUT",
                    "level": level.upper(),
                    "price": resistance,
                    "description": f"Price broke above {level.upper()} resistance at ₹{resistance}",
                    "strength": 4 if level == "r1" else 5
                }
        
        # Check S1, S2, S3 breakdowns
        for level in ["s1", "s2", "s3"]:
            support = pivots.get(level, 0)
            if previous_price > support >= current_price:
                return {
                    "type": "SUPPORT_BREAKDOWN",
                    "level": level.upper(),
                    "price": support,
                    "description": f"Price broke below {level.upper()} support at ₹{support}",
                    "strength": 4 if level == "s1" else 5
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Error detecting pivot breakout: {e}")
        return None
