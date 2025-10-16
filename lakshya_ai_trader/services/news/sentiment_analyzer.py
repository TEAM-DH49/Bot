"""
News Sentiment Analyzer
Analyze sentiment of news headlines and articles
"""
import logging
from typing import Dict, Any, List
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

from config.constants import POSITIVE_KEYWORDS, NEGATIVE_KEYWORDS

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Analyze sentiment of news and text"""
    
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text using multiple methods
        
        Args:
            text: Text to analyze
        
        Returns:
            Dict with sentiment scores and classification
        """
        if not text:
            return {
                "score": 0.0,
                "sentiment": "NEUTRAL",
                "confidence": 0.0
            }
        
        # Method 1: VADER sentiment
        vader_scores = self.vader.polarity_scores(text)
        vader_compound = vader_scores["compound"]
        
        # Method 2: TextBlob sentiment
        try:
            blob = TextBlob(text)
            textblob_score = blob.sentiment.polarity
        except:
            textblob_score = 0.0
        
        # Method 3: Keyword-based sentiment
        keyword_score = self._keyword_sentiment(text)
        
        # Combine scores (weighted average)
        combined_score = (
            vader_compound * 0.4 +
            textblob_score * 0.3 +
            keyword_score * 0.3
        )
        
        # Classify sentiment
        if combined_score >= 0.2:
            sentiment = "POSITIVE"
            emoji = "😊"
        elif combined_score <= -0.2:
            sentiment = "NEGATIVE"
            emoji = "😞"
        else:
            sentiment = "NEUTRAL"
            emoji = "😐"
        
        # Calculate confidence based on agreement
        scores_list = [vader_compound, textblob_score, keyword_score]
        agreement = sum(1 for s in scores_list if (s > 0.1) == (combined_score > 0.1))
        confidence = agreement / len(scores_list)
        
        return {
            "score": round(combined_score, 3),
            "sentiment": sentiment,
            "emoji": emoji,
            "confidence": round(confidence, 2),
            "vader": round(vader_compound, 2),
            "textblob": round(textblob_score, 2),
            "keyword": round(keyword_score, 2)
        }
    
    def _keyword_sentiment(self, text: str) -> float:
        """
        Calculate sentiment based on keyword matching
        
        Args:
            text: Text to analyze
        
        Returns:
            Sentiment score (-1 to 1)
        """
        text_lower = text.lower()
        words = re.findall(r'\w+', text_lower)
        
        if not words:
            return 0.0
        
        positive_count = sum(1 for word in words if word in [k.lower() for k in POSITIVE_KEYWORDS])
        negative_count = sum(1 for word in words if word in [k.lower() for k in NEGATIVE_KEYWORDS])
        
        if positive_count + negative_count == 0:
            return 0.0
        
        score = (positive_count - negative_count) / len(words) * 10
        
        # Normalize to -1 to 1 range
        return max(-1.0, min(1.0, score))
    
    def analyze_headlines(self, headlines: List[str]) -> Dict[str, Any]:
        """
        Analyze sentiment of multiple headlines
        
        Args:
            headlines: List of news headlines
        
        Returns:
            Aggregate sentiment analysis
        """
        if not headlines:
            return {
                "overall_score": 0.0,
                "overall_sentiment": "NEUTRAL",
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0
            }
        
        scores = []
        sentiments = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
        
        for headline in headlines:
            result = self.analyze_text(headline)
            scores.append(result["score"])
            sentiments[result["sentiment"]] += 1
        
        overall_score = sum(scores) / len(scores) if scores else 0.0
        
        # Determine overall sentiment
        if overall_score >= 0.15:
            overall_sentiment = "POSITIVE"
            emoji = "😊"
        elif overall_score <= -0.15:
            overall_sentiment = "NEGATIVE"
            emoji = "😞"
        else:
            overall_sentiment = "NEUTRAL"
            emoji = "😐"
        
        return {
            "overall_score": round(overall_score, 3),
            "overall_sentiment": overall_sentiment,
            "emoji": emoji,
            "positive_count": sentiments["POSITIVE"],
            "negative_count": sentiments["NEGATIVE"],
            "neutral_count": sentiments["NEUTRAL"],
            "total_headlines": len(headlines),
            "individual_scores": [round(s, 2) for s in scores]
        }
    
    def analyze_news_articles(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze sentiment of news articles
        
        Args:
            articles: List of article dicts with 'title' and optionally 'summary'
        
        Returns:
            Sentiment analysis results
        """
        headlines = []
        
        for article in articles:
            title = article.get("title", "")
            summary = article.get("summary", "")
            
            # Combine title and summary for more context
            text = f"{title}. {summary}" if summary else title
            headlines.append(text)
        
        return self.analyze_headlines(headlines)
    
    def get_sentiment_emoji(self, score: float) -> str:
        """Get emoji for sentiment score"""
        if score >= 0.5:
            return "😁"  # Very positive
        elif score >= 0.2:
            return "😊"  # Positive
        elif score <= -0.5:
            return "😢"  # Very negative
        elif score <= -0.2:
            return "😞"  # Negative
        else:
            return "😐"  # Neutral
    
    def get_sentiment_description(self, sentiment: str, score: float) -> str:
        """Get human-readable sentiment description"""
        if sentiment == "POSITIVE":
            if score >= 0.5:
                return "Very positive news sentiment"
            else:
                return "Moderately positive news sentiment"
        elif sentiment == "NEGATIVE":
            if score <= -0.5:
                return "Very negative news sentiment"
            else:
                return "Moderately negative news sentiment"
        else:
            return "Neutral news sentiment"


# Global instance
sentiment_analyzer = SentimentAnalyzer()
