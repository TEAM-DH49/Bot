"""
Message Formatters
Format bot messages beautifully with emojis and proper structure
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def format_number(num: float, decimals: int = 2) -> str:
    """Format number with Indian comma notation"""
    try:
        if num >= 10000000:  # 1 Crore
            return f"{num/10000000:.{decimals}f}Cr"
        elif num >= 100000:  # 1 Lakh
            return f"{num/100000:.{decimals}f}L"
        elif num >= 1000:  # 1 Thousand
            return f"{num/1000:.{decimals}f}K"
        else:
            return f"{num:.{decimals}f}"
    except:
        return str(num)


def format_price(price: float) -> str:
    """Format price with rupee symbol"""
    return f"₹{price:,.2f}"


def format_percentage(pct: float) -> str:
    """Format percentage with + or - sign"""
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"


def get_change_emoji(change: float) -> str:
    """Get emoji based on price change"""
    if change > 2:
        return "🚀"
    elif change > 0:
        return "🟢"
    elif change < -2:
        return "📉"
    elif change < 0:
        return "🔴"
    else:
        return "⚪"


def format_stock_quote(data: Dict[str, Any]) -> str:
    """
    Format stock quote message
    
    Args:
        data: Stock data dict
    
    Returns:
        Formatted message string
    """
    try:
        symbol = data.get("symbol", "N/A")
        price = data.get("price", 0)
        change = data.get("change", 0)
        change_pct = data.get("change_pct", 0)
        volume = data.get("volume", 0)
        open_price = data.get("open", 0)
        high = data.get("high", 0)
        low = data.get("low", 0)
        prev_close = data.get("previous_close", 0)
        
        emoji = get_change_emoji(change_pct)
        
        message = f"""
📈 <b>{symbol}</b> {emoji}

💰 <b>Current Price:</b> {format_price(price)}
📊 <b>Change:</b> {format_price(change)} ({format_percentage(change_pct)})

<b>Day's Range:</b>
   Open: {format_price(open_price)}
   High: {format_price(high)}
   Low: {format_price(low)}
   Prev Close: {format_price(prev_close)}

📦 <b>Volume:</b> {format_number(volume)}

⏰ <i>Updated: {datetime.now().strftime("%H:%M:%S IST")}</i>
"""
        
        return message.strip()
        
    except Exception as e:
        logger.error(f"Error formatting stock quote: {e}")
        return "Error formatting stock data"


def format_technical_analysis(symbol: str, indicators: Dict[str, Any]) -> str:
    """
    Format technical analysis message
    
    Args:
        symbol: Stock symbol
        indicators: Dict with RSI, MACD, Bollinger Bands, etc.
    
    Returns:
        Formatted message
    """
    try:
        message = f"📊 <b>Technical Analysis: {symbol}</b>\n\n"
        
        # RSI
        if "rsi" in indicators:
            rsi = indicators["rsi"]
            rsi_signal = indicators.get("rsi_signal", {})
            emoji = rsi_signal.get("emoji", "⚪")
            message += f"<b>RSI (14):</b> {rsi} {emoji}\n"
            message += f"   {rsi_signal.get('description', 'N/A')}\n\n"
        
        # MACD
        if "macd" in indicators:
            macd = indicators["macd"]
            macd_signal = indicators.get("macd_signal", {})
            emoji = macd_signal.get("emoji", "⚪")
            message += f"<b>MACD:</b> {macd.get('signal_type', 'N/A')} {emoji}\n"
            message += f"   Line: {macd.get('macd_line', 0):.2f}\n"
            message += f"   Signal: {macd.get('signal_line', 0):.2f}\n"
            if macd.get("crossover"):
                message += f"   🔔 {macd['crossover'].replace('_', ' ').title()}\n"
            message += "\n"
        
        # EMAs
        if "emas" in indicators:
            emas = indicators["emas"]
            message += f"<b>Moving Averages:</b>\n"
            for period, value in sorted(emas.items()):
                message += f"   EMA{period}: {format_price(value)}\n"
            message += "\n"
        
        # Bollinger Bands
        if "bollinger" in indicators:
            bb = indicators["bollinger"]
            message += f"<b>Bollinger Bands:</b>\n"
            message += f"   Upper: {format_price(bb.get('upper_band', 0))}\n"
            message += f"   Middle: {format_price(bb.get('middle_band', 0))}\n"
            message += f"   Lower: {format_price(bb.get('lower_band', 0))}\n"
            message += f"   Signal: {bb.get('signal', 'N/A')}\n\n"
        
        # Pivot Points
        if "pivots" in indicators:
            pivots = indicators["pivots"]
            message += f"<b>Pivot Points:</b>\n"
            message += f"   R3: {format_price(pivots.get('r3', 0))}\n"
            message += f"   R2: {format_price(pivots.get('r2', 0))}\n"
            message += f"   R1: {format_price(pivots.get('r1', 0))}\n"
            message += f"   PP: {format_price(pivots.get('pivot', 0))}\n"
            message += f"   S1: {format_price(pivots.get('s1', 0))}\n"
            message += f"   S2: {format_price(pivots.get('s2', 0))}\n"
            message += f"   S3: {format_price(pivots.get('s3', 0))}\n\n"
        
        # Volume Analysis
        if "volume" in indicators:
            vol = indicators["volume"]
            message += f"<b>Volume Analysis:</b>\n"
            message += f"   {vol.get('signal', 'N/A')}\n"
            message += f"   Current: {format_number(vol.get('current_volume', 0))}\n"
            message += f"   Average: {format_number(vol.get('average_volume', 0))}\n"
            message += f"   Ratio: {vol.get('volume_ratio', 0):.2f}x\n\n"
        
        message += f"⏰ <i>{datetime.now().strftime('%d-%m-%Y %H:%M IST')}</i>"
        
        return message.strip()
        
    except Exception as e:
        logger.error(f"Error formatting technical analysis: {e}")
        return "Error formatting technical analysis"


def format_news_list(symbol: str, articles: List[Dict[str, Any]], sentiment: Dict[str, Any] = None) -> str:
    """Format news articles list"""
    try:
        message = f"📰 <b>Latest News: {symbol}</b>\n\n"
        
        if sentiment:
            emoji = sentiment.get("emoji", "😐")
            overall = sentiment.get("overall_sentiment", "NEUTRAL")
            score = sentiment.get("overall_score", 0)
            message += f"<b>Overall Sentiment:</b> {overall} {emoji} ({score:+.2f})\n\n"
        
        for i, article in enumerate(articles[:10], 1):
            title = article.get("title", "No title")
            url = article.get("url", "")
            source = article.get("source", "Unknown")
            
            # Truncate long titles
            if len(title) > 80:
                title = title[:77] + "..."
            
            message += f"{i}. <a href='{url}'>{title}</a>\n"
            message += f"   <i>Source: {source}</i>\n\n"
        
        message += "⚠️ <i>News for informational purposes only</i>"
        
        return message.strip()
        
    except Exception as e:
        logger.error(f"Error formatting news: {e}")
        return "Error formatting news"


def format_watchlist(watchlist: List[Dict[str, Any]]) -> str:
    """Format watchlist message"""
    try:
        if not watchlist:
            return "📝 <b>Your Watchlist is empty</b>\n\nAdd stocks using /watchlist add SYMBOL"
        
        message = f"📝 <b>Your Watchlist</b> ({len(watchlist)} stocks)\n\n"
        
        for stock in watchlist:
            symbol = stock.get("symbol", "N/A")
            price = stock.get("price", 0)
            change_pct = stock.get("change_pct", 0)
            emoji = get_change_emoji(change_pct)
            
            message += f"{emoji} <b>{symbol}</b>\n"
            message += f"   {format_price(price)} ({format_percentage(change_pct)})\n\n"
        
        return message.strip()
        
    except Exception as e:
        logger.error(f"Error formatting watchlist: {e}")
        return "Error formatting watchlist"


def format_portfolio(portfolio: List[Dict[str, Any]], total_value: float, total_pl: float) -> str:
    """Format portfolio message"""
    try:
        if not portfolio:
            return "💼 <b>Your Portfolio is empty</b>\n\nAdd holdings using /portfolio add SYMBOL QUANTITY BUY_PRICE"
        
        message = f"💼 <b>Your Portfolio</b>\n\n"
        message += f"<b>Total Value:</b> {format_price(total_value)}\n"
        message += f"<b>Total P/L:</b> {format_price(total_pl)} ({format_percentage(total_pl/total_value*100)})\n\n"
        
        for holding in portfolio:
            symbol = holding.get("symbol", "N/A")
            quantity = holding.get("quantity", 0)
            buy_price = holding.get("buy_price", 0)
            current_price = holding.get("current_price", 0)
            pl = holding.get("pl", 0)
            pl_pct = holding.get("pl_pct", 0)
            emoji = get_change_emoji(pl_pct)
            
            message += f"{emoji} <b>{symbol}</b>\n"
            message += f"   Qty: {quantity} @ {format_price(buy_price)}\n"
            message += f"   Current: {format_price(current_price)}\n"
            message += f"   P/L: {format_price(pl)} ({format_percentage(pl_pct)})\n\n"
        
        return message.strip()
        
    except Exception as e:
        logger.error(f"Error formatting portfolio: {e}")
        return "Error formatting portfolio"


def format_scanner_results(results: List[Dict[str, Any]]) -> str:
    """Format scanner results message"""
    try:
        if not results:
            return "🔍 <b>Scanner Results</b>\n\nNo signals found at this time."
        
        message = f"🔍 <b>Scanner Results</b> ({len(results)} signals)\n\n"
        
        for result in results[:15]:  # Limit to 15
            symbol = result.get("symbol", "N/A")
            signal_type = result.get("signal_type", "N/A")
            price = result.get("price", 0)
            description = result.get("description", "")
            
            if "oversold" in signal_type.lower():
                emoji = "🔴"
            elif "overbought" in signal_type.lower():
                emoji = "🟢"
            elif "bullish" in signal_type.lower():
                emoji = "🚀"
            elif "bearish" in signal_type.lower():
                emoji = "📉"
            else:
                emoji = "⚡"
            
            message += f"{emoji} <b>{symbol}</b> - {format_price(price)}\n"
            message += f"   Signal: {signal_type.replace('_', ' ').title()}\n"
            if description:
                message += f"   {description}\n"
            message += "\n"
        
        message += "⚠️ <i>Signals are educational, not trading advice</i>"
        
        return message.strip()
        
    except Exception as e:
        logger.error(f"Error formatting scanner results: {e}")
        return "Error formatting scanner results"


def format_indices(indices_data: Dict[str, Dict[str, Any]]) -> str:
    """Format market indices message"""
    try:
        message = "📊 <b>Market Indices</b>\n\n"
        
        for name, data in indices_data.items():
            price = data.get("price", 0)
            change = data.get("change", 0)
            change_pct = data.get("change_pct", 0)
            emoji = get_change_emoji(change_pct)
            
            message += f"{emoji} <b>{name}</b>\n"
            message += f"   {price:,.2f} ({format_percentage(change_pct)})\n\n"
        
        message += f"⏰ <i>{datetime.now().strftime('%d-%m-%Y %H:%M IST')}</i>"
        
        return message.strip()
        
    except Exception as e:
        logger.error(f"Error formatting indices: {e}")
        return "Error formatting indices"
