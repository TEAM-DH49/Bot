"""
AI Prompt Templates
All prompt templates for different AI analysis tasks
"""
from typing import Dict, Any


def build_stock_analysis_prompt(symbol: str, data: Dict[str, Any]) -> str:
    """
    Build comprehensive stock analysis prompt
    
    Args:
        symbol: Stock symbol
        data: Dict containing price, indicators, volume, news
    
    Returns:
        Formatted prompt string
    """
    price = data.get("price", 0)
    change_pct = data.get("change_pct", 0)
    rsi = data.get("rsi", "N/A")
    macd_signal = data.get("macd_signal", "N/A")
    volume_analysis = data.get("volume_analysis", "Normal")
    
    prompt = f"""
Stock: {symbol}
Current Price: ₹{price}
Today's Change: {change_pct:+.2f}%

Technical Indicators:
- RSI: {rsi}
- MACD: {macd_signal}
- Volume: {volume_analysis}

Analyze this stock in 3-4 concise points:
1. Current technical setup (kya dikha raha hai?)
2. Short-term outlook (agle kuch dino mein kya expect kar sakte hai?)
3. Key price level to watch (kis level ko dhyan se dekhna chahiye?)

Keep it simple and educational. Use Hindi-English mix naturally.
"""
    
    return prompt.strip()


SIGNAL_EXPLANATION_PROMPT = """
Stock: {symbol}
Signal: {signal_type}
Details: {details}

Explain this signal to a beginner trader in 2-3 simple sentences.
What does this mean? Should they pay attention to this?
Use Hindi-English mix.
"""


MARKET_SUMMARY_PROMPT = """
Market Summary:
NIFTY 50: {nifty_change}%
SENSEX: {sensex_change}%

Top Gainers:
{top_gainers}

Top Losers:
{top_losers}

Key News:
{news_headlines}

Provide a brief market summary in 4-5 sentences:
1. Overall market mood
2. Sector performance
3. What drove today's movement
4. What to watch tomorrow

Use professional yet conversational Hindi-English tone.
"""


NEWS_SENTIMENT_PROMPT = """
Stock: {symbol}
Recent News Headlines:
{headlines}

Analyze the overall news sentiment:
1. Is it positive, negative, or neutral?
2. What's the main theme in the news?
3. Should traders pay attention to this?

Keep it brief (3 sentences max).
"""


PATTERN_DETECTION_PROMPT = """
Stock: {symbol}
Price Data (Last 30 days):
{price_data}

Technical Setup:
- RSI: {rsi}
- MACD: {macd}
- Volume Trend: {volume_trend}

Identify any chart patterns (double bottom, head & shoulders, triangle, etc.).
Explain what pattern you see and what it typically means.
If no clear pattern, say "No obvious pattern".

Keep response educational and brief (3-4 sentences).
"""


PORTFOLIO_ANALYSIS_PROMPT = """
Portfolio Holdings:
{holdings}

Total Portfolio Value: ₹{total_value}
Day's Change: {day_change}%
Overall P/L: {total_pl}%

Provide brief portfolio commentary:
1. Overall health of portfolio
2. Any positions that need attention
3. Diversification assessment

Keep it constructive and educational (4-5 sentences).
"""


BACKTEST_INTERPRETATION_PROMPT = """
Backtest Results for {symbol}:
Strategy: {strategy}
Period: {start_date} to {end_date}

Results:
- Total Return: {total_return}%
- Win Rate: {win_rate}%
- Total Trades: {total_trades}
- Max Drawdown: {max_drawdown}%

Interpret these results:
1. Was the strategy profitable?
2. Is the win rate acceptable?
3. What does the drawdown tell us?
4. Would you recommend this strategy?

Be honest and educational (4-5 sentences).
"""


COMPARE_STOCKS_PROMPT = """
Stock Comparison:
{comparison_data}

Compare these stocks and tell me:
1. Which looks technically stronger?
2. Which has better momentum?
3. Any standout differences?

Keep it brief and actionable (3-4 sentences).
"""


CONVERSATIONAL_PROMPT = """
User asked: "{user_question}"

{context}

Answer their question in a friendly, conversational Hindi-English mix.
Be helpful and educational. If it's about specific stocks, use the context provided.
Always end with: "⚠️ Yeh educational information hai, financial advice nahi."
"""


DAILY_DIGEST_MORNING_PROMPT = """
Good morning! Here's today's market outlook:

Global Markets:
{global_summary}

Indian Markets:
Pre-market: {premarket_data}

Stocks in Focus:
{focus_stocks}

Key Events Today:
{key_events}

Write a brief morning market brief in conversational tone (5-6 sentences).
What should traders watch today?
"""


DAILY_DIGEST_CLOSING_PROMPT = """
Market Closing Summary:

NIFTY 50: {nifty_performance}
SENSEX: {sensex_performance}

Today's Action:
Top Gainers: {top_gainers}
Top Losers: {top_losers}
Most Active: {most_active}

Market Breadth: {breadth}
FII/DII Activity: {fii_dii}

Summarize today's market in 5-6 sentences:
1. What happened today?
2. Which sectors moved?
3. Any notable events?
4. What to watch tomorrow?

Keep tone professional yet friendly.
"""


def format_holdings_for_prompt(holdings: list) -> str:
    """Format portfolio holdings for AI prompt"""
    lines = []
    for holding in holdings:
        lines.append(
            f"- {holding['symbol']}: {holding['quantity']} shares @ ₹{holding['buy_price']} "
            f"(Current: ₹{holding['current_price']}, P/L: {holding['pl_pct']:+.2f}%)"
        )
    return "\n".join(lines)


def format_comparison_for_prompt(stocks: dict) -> str:
    """Format stock comparison data for AI prompt"""
    lines = []
    for symbol, data in stocks.items():
        lines.append(f"""
{symbol}:
- Price: ₹{data['price']} ({data['change_pct']:+.2f}%)
- RSI: {data.get('rsi', 'N/A')}
- MACD: {data.get('macd_signal', 'N/A')}
- Volume: {data.get('volume_analysis', 'N/A')}
""")
    return "\n".join(lines)


# System prompts for different contexts
SYSTEM_PROMPT_TRADER = """You are an expert Indian stock market analyst and educator.
Your role is to explain technical analysis and market concepts in simple terms.
Use natural Hindi-English mix (Hinglish) to connect with Indian traders.
CRITICAL: Never give buy/sell recommendations. Only explain what data suggests.
Always be educational, not prescriptive.
Keep responses concise and actionable."""


SYSTEM_PROMPT_NEWS = """You are a financial news analyst.
Analyze news sentiment objectively without bias.
Identify key themes and implications.
Be factual and balanced."""


SYSTEM_PROMPT_EDUCATOR = """You are a stock market educator.
Explain concepts clearly for beginners.
Use analogies and examples from daily life.
Encourage learning and understanding."""


SYSTEM_PROMPT_CASUAL = """You are a friendly stock market assistant.
Chat naturally in Hindi-English mix.
Be helpful, patient, and encouraging.
Make finance accessible and less intimidating."""
