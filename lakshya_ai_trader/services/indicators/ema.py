"""
EMA (Exponential Moving Average) Calculator
Gives more weight to recent prices
"""
import logging
from typing import Dict, Any, Optional, List
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_ema(prices: pd.Series, period: int) -> Optional[float]:
    """
    Calculate current EMA value
    
    Args:
        prices: Price series
        period: EMA period
    
    Returns:
        Current EMA value
    """
    try:
        if len(prices) < period:
            return None
        
        ema = prices.ewm(span=period, adjust=False).mean()
        return round(float(ema.iloc[-1]), 2)
        
    except Exception as e:
        logger.error(f"Error calculating EMA: {e}")
        return None


def calculate_multiple_emas(prices: pd.Series, periods: List[int] = [20, 50, 200]) -> Dict[int, float]:
    """
    Calculate multiple EMAs at once
    
    Args:
        prices: Price series
        periods: List of EMA periods
    
    Returns:
        Dict mapping period to EMA value
    """
    results = {}
    
    for period in periods:
        ema = calculate_ema(prices, period)
        if ema:
            results[period] = ema
    
    return results


def get_ema_crossover_signal(
    prices: pd.Series,
    fast_period: int = 20,
    slow_period: int = 50
) -> Optional[Dict[str, Any]]:
    """
    Detect EMA crossover signals
    
    Golden Cross: Fast EMA crosses above slow EMA (Bullish)
    Death Cross: Fast EMA crosses below slow EMA (Bearish)
    
    Args:
        prices: Price series
        fast_period: Fast EMA period
        slow_period: Slow EMA period
    
    Returns:
        Crossover signal info or None
    """
    try:
        if len(prices) < slow_period + 2:
            return None
        
        fast_ema = prices.ewm(span=fast_period, adjust=False).mean()
        slow_ema = prices.ewm(span=slow_period, adjust=False).mean()
        
        # Current values
        current_fast = fast_ema.iloc[-1]
        current_slow = slow_ema.iloc[-1]
        
        # Previous values
        prev_fast = fast_ema.iloc[-2]
        prev_slow = slow_ema.iloc[-2]
        
        # Detect crossovers
        if prev_fast <= prev_slow and current_fast > current_slow:
            return {
                "type": "GOLDEN_CROSS",
                "description": f"🟢 Golden Cross: EMA{fast_period} crossed above EMA{slow_period}",
                "fast_ema": round(float(current_fast), 2),
                "slow_ema": round(float(current_slow), 2),
                "signal": "BULLISH",
                "strength": 5
            }
        elif prev_fast >= prev_slow and current_fast < current_slow:
            return {
                "type": "DEATH_CROSS",
                "description": f"🔴 Death Cross: EMA{fast_period} crossed below EMA{slow_period}",
                "fast_ema": round(float(current_fast), 2),
                "slow_ema": round(float(current_slow), 2),
                "signal": "BEARISH",
                "strength": 5
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error detecting EMA crossover: {e}")
        return None


def get_price_ema_position(price: float, emas: Dict[int, float]) -> Dict[str, Any]:
    """
    Analyze price position relative to EMAs
    
    Args:
        price: Current price
        emas: Dict of EMA values
    
    Returns:
        Position analysis
    """
    try:
        above_all = all(price > ema for ema in emas.values())
        below_all = all(price < ema for ema in emas.values())
        
        if above_all:
            return {
                "position": "STRONG_BULLISH",
                "description": "Price above all EMAs - Strong uptrend",
                "emoji": "🟢🟢",
                "strength": 5
            }
        elif below_all:
            return {
                "position": "STRONG_BEARISH",
                "description": "Price below all EMAs - Strong downtrend",
                "emoji": "🔴🔴",
                "strength": 5
            }
        else:
            # Count how many EMAs price is above
            above_count = sum(1 for ema in emas.values() if price > ema)
            total = len(emas)
            
            if above_count > total / 2:
                return {
                    "position": "BULLISH",
                    "description": f"Price above {above_count}/{total} EMAs - Bullish",
                    "emoji": "🟢",
                    "strength": 3
                }
            else:
                return {
                    "position": "BEARISH",
                    "description": f"Price below {total - above_count}/{total} EMAs - Bearish",
                    "emoji": "🔴",
                    "strength": 3
                }
        
    except Exception as e:
        logger.error(f"Error analyzing price-EMA position: {e}")
        return {}


def detect_ema_alignment(emas: Dict[int, float]) -> Optional[str]:
    """
    Detect if EMAs are aligned (bullish or bearish)
    
    Bullish alignment: Faster EMAs above slower EMAs
    Bearish alignment: Faster EMAs below slower EMAs
    
    Args:
        emas: Dict of EMAs {period: value}
    
    Returns:
        "BULLISH", "BEARISH", or None
    """
    try:
        sorted_emas = sorted(emas.items(), key=lambda x: x[0])
        
        if len(sorted_emas) < 2:
            return None
        
        # Check if aligned (each faster EMA is above/below slower EMA)
        bullish = all(
            sorted_emas[i][1] > sorted_emas[i + 1][1]
            for i in range(len(sorted_emas) - 1)
        )
        
        bearish = all(
            sorted_emas[i][1] < sorted_emas[i + 1][1]
            for i in range(len(sorted_emas) - 1)
        )
        
        if bullish:
            return "BULLISH"
        elif bearish:
            return "BEARISH"
        else:
            return None
        
    except Exception as e:
        logger.error(f"Error detecting EMA alignment: {e}")
        return None
