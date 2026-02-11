"""Lightweight sentiment analysis using VADER.

VADER is optimized for social media text and runs locally with no API calls.
English-focused; non-English text will tend toward neutral scores.
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(text: str) -> dict:
    """Analyze sentiment of text.

    Returns:
        dict with keys:
            sentiment: "positive" | "negative" | "neutral"
            score: float between -1.0 and 1.0 (compound score)
    """
    if not text or not text.strip():
        return {"sentiment": "neutral", "score": 0.0}

    scores = _analyzer.polarity_scores(text)
    compound = scores["compound"]

    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return {"sentiment": label, "score": round(compound, 4)}
