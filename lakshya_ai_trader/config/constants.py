"""
Market Constants and Symbol Lists
All Indian stock market related constants
"""

# NSE and BSE suffixes
NSE_SUFFIX = ".NS"
BSE_SUFFIX = ".BO"

# NIFTY 50 Stocks
NIFTY_50_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK",
    "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "SUNPHARMA",
    "TITAN", "ULTRACEMCO", "BAJFINANCE", "NESTLEIND", "DMART",
    "HCLTECH", "WIPRO", "ADANIENT", "ADANIPORTS", "NTPC",
    "ONGC", "POWERGRID", "TATAMOTORS", "TATASTEEL", "TECHM",
    "INDUSINDBK", "BAJAJFINSV", "M&M", "DRREDDY", "COALINDIA",
    "JSWSTEEL", "GRASIM", "BRITANNIA", "DIVISLAB", "CIPLA",
    "EICHERMOT", "HEROMOTOCO", "TATACONSUM", "APOLLOHOSP", "HINDALCO",
    "BAJAJ-AUTO", "SHREECEM", "UPL", "BPCL", "SBILIFE"
]

# SENSEX 30 Stocks
SENSEX_30_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK",
    "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "SUNPHARMA",
    "TITAN", "ULTRACEMCO", "BAJFINANCE", "NESTLEIND", "WIPRO",
    "NTPC", "POWERGRID", "TATAMOTORS", "TATASTEEL", "TECHM",
    "INDUSINDBK", "M&M", "BAJAJFINSV", "JSWSTEEL", "MARUTI"
]

# Symbol corrections (common user mistakes)
SYMBOL_CORRECTIONS = {
    "TATA": "TATAMOTORS",
    "IT": "ITC",
    "RELIANCE": "RELIANCE",
    "INFOSYS": "INFY",
    "WIPRO": "WIPRO",
    "HDFC": "HDFCBANK",
    "ICICI": "ICICIBANK",
    "SBI": "SBIN",
    "AIRTEL": "BHARTIARTL",
    "KOTAK": "KOTAKBANK",
    "AXIS": "AXISBANK",
    "M&M": "M&M",
    "MARUTI": "MARUTI",
    "HINDUNILEVER": "HINDUNILVR",
}

# Indian Market Indices
INDICES = {
    "NIFTY 50": "^NSEI",
    "NIFTY BANK": "^NSEBANK",
    "SENSEX": "^BSESN",
    "NIFTY IT": "^CNXIT",
    "NIFTY AUTO": "^CNXAUTO",
    "NIFTY PHARMA": "^CNXPHARMA",
    "NIFTY FMCG": "^CNXFMCG",
    "NIFTY METAL": "^CNXMETAL",
    "NIFTY REALTY": "^CNXREALTY",
    "NIFTY ENERGY": "^CNXENERGY",
    "NIFTY MEDIA": "^CNXMEDIA",
}

# Technical Indicator Thresholds
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
RSI_EXTREME_OVERSOLD = 20
RSI_EXTREME_OVERBOUGHT = 80

# MACD Parameters
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Bollinger Bands Parameters
BB_PERIOD = 20
BB_STD_DEV = 2

# EMA Periods
EMA_PERIODS = [20, 50, 200]

# Timeframes
TIMEFRAMES = {
    "1m": "1 minute",
    "5m": "5 minutes",
    "15m": "15 minutes",
    "30m": "30 minutes",
    "1h": "1 hour",
    "1d": "1 day",
    "1wk": "1 week",
    "1mo": "1 month"
}

# Sectors
SECTORS = {
    "BANKING": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK", "INDUSINDBK"],
    "IT": ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM"],
    "AUTO": ["MARUTI", "TATAMOTORS", "M&M", "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO"],
    "PHARMA": ["SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "APOLLOHOSP"],
    "ENERGY": ["RELIANCE", "ONGC", "BPCL", "NTPC", "POWERGRID", "COALINDIA"],
    "FMCG": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "TATACONSUM"],
    "METALS": ["TATASTEEL", "JSWSTEEL", "HINDALCO", "COALINDIA", "VEDL"],
    "TELECOM": ["BHARTIARTL", "RELIANCE"],
}

# Sentiment Keywords
POSITIVE_KEYWORDS = [
    "beats", "growth", "profit", "surge", "upgrade", "rally",
    "bullish", "strong", "gains", "positive", "rise", "soar",
    "record", "high", "success", "outperform", "breakthrough",
    "expansion", "acquisition", "deal", "dividend", "buyback"
]

NEGATIVE_KEYWORDS = [
    "loss", "decline", "miss", "weak", "downgrade", "fall",
    "bearish", "crash", "plunge", "negative", "drop", "slump",
    "low", "failure", "concern", "underperform", "debt",
    "lawsuit", "scandal", "warning", "cut", "layoff"
]

# Alert Condition Types
ALERT_CONDITIONS = {
    "ABOVE": "Price crosses above target",
    "BELOW": "Price crosses below target",
    "RSI_ABOVE": "RSI goes above threshold",
    "RSI_BELOW": "RSI goes below threshold",
    "VOLUME_SPIKE": "Volume exceeds threshold",
    "PERCENTAGE_GAIN": "Price gains percentage",
    "PERCENTAGE_LOSS": "Price loses percentage"
}

# Chart Patterns
CHART_PATTERNS = [
    "Double Bottom",
    "Double Top",
    "Head and Shoulders",
    "Inverse Head and Shoulders",
    "Ascending Triangle",
    "Descending Triangle",
    "Symmetrical Triangle",
    "Cup and Handle",
    "Flag Pattern",
    "Pennant Pattern",
    "Wedge Pattern"
]

# Support/Resistance Calculation Methods
SR_METHODS = ["pivot_points", "fibonacci", "psychological_levels"]

# Volume Analysis Thresholds
VOLUME_SPIKE_MULTIPLIER = 2.0
HIGH_VOLUME_THRESHOLD = 1.5
LOW_VOLUME_THRESHOLD = 0.5

# Cache Keys
CACHE_KEYS = {
    "QUOTE": "quote:{}",
    "INDICATORS": "indicators:{}",
    "NEWS": "news:{}",
    "AI_ANALYSIS": "ai:{}",
    "SCANNER_RESULTS": "scanner:results",
    "MARKET_STATUS": "market:status",
    "USER_RATE_LIMIT": "rate:{}:{}",  # user_id, minute
}

# Cache TTL (seconds)
CACHE_TTL = {
    "QUOTE": 60,
    "INDICATORS": 300,  # 5 minutes
    "NEWS": 1800,  # 30 minutes
    "AI_ANALYSIS": 300,
    "SCANNER_RESULTS": 3600,  # 1 hour
    "MARKET_STATUS": 60,
}

# API Rate Limits (per day)
API_LIMITS = {
    "ALPHA_VANTAGE_FREE": 25,
    "FINNHUB_FREE": 60,  # per minute
    "TWELVE_DATA_FREE": 800,
}

# Messages - English
MESSAGES_EN = {
    "START": "🎯 Welcome to Lakshya AI Trader!\n\nYour personal Indian stock market analysis bot powered by AI.\n\nUse /help to see available commands.",
    "HELP": "📚 Available Commands:\n\n/quote SYMBOL - Get live stock price\n/ta SYMBOL - Technical analysis\n/ai SYMBOL - AI-powered insights\n/alert - Manage price alerts\n/watchlist - Manage your watchlist\n/portfolio - Track your holdings\n/news SYMBOL - Latest news\n/scanner - Find trading opportunities\n/indices - Market indices\n/sectors - Sector performance\n/compare - Compare stocks\n/options - Options chain data\n/digest - Toggle daily digest\n/help - Show this message",
    "INVALID_SYMBOL": "❌ Invalid symbol. Please use NSE symbols like RELIANCE, TCS, INFY",
    "RATE_LIMIT": "⚠️ Too many requests. Please wait {} seconds.",
    "ERROR": "❌ An error occurred. Please try again later.",
    "MARKET_CLOSED": "🔒 Market is closed. Data may not be real-time.",
    "DISCLAIMER": "⚠️ Educational purpose only. Not financial advice.",
}

# Messages - Hindi
MESSAGES_HI = {
    "START": "🎯 लक्ष्य एआई ट्रेडर में आपका स्वागत है!\n\nआपका निजी भारतीय शेयर बाजार विश्लेषण बॉट।\n\nकमांड देखने के लिए /help का उपयोग करें।",
    "HELP": "📚 उपलब्ध कमांड:\n\n/quote SYMBOL - लाइव स्टॉक प्राइस\n/ta SYMBOL - तकनीकी विश्लेषण\n/ai SYMBOL - एआई इनसाइट्स\n/alert - प्राइस अलर्ट\n/watchlist - वॉचलिस्ट प्रबंधन\n/portfolio - होल्डिंग्स ट्रैक करें\n/news SYMBOL - ताजा खबरें\n/scanner - ट्रेडिंग अवसर\n/indices - बाजार सूचकांक\n/sectors - सेक्टर प्रदर्शन\n/compare - स्टॉक तुलना\n/options - ऑप्शंस चेन\n/help - यह संदेश",
    "INVALID_SYMBOL": "❌ अमान्य सिंबल। कृपया RELIANCE, TCS, INFY जैसे NSE सिंबल का उपयोग करें",
    "RATE_LIMIT": "⚠️ बहुत अधिक अनुरोध। कृपया {} सेकंड प्रतीक्षा करें।",
    "ERROR": "❌ एक त्रुटि हुई। कृपया बाद में पुनः प्रयास करें।",
    "MARKET_CLOSED": "🔒 बाजार बंद है। डेटा वास्तविक समय का नहीं हो सकता।",
    "DISCLAIMER": "⚠️ केवल शैक्षिक उद्देश्य। वित्तीय सलाह नहीं।",
}
