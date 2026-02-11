"""Tests for the sentiment analyzer service."""

from app.services.sentiment_analyzer import analyze_sentiment


class TestAnalyzeSentiment:
    """Tests for analyze_sentiment function."""

    def test_positive_text(self):
        result = analyze_sentiment("This is amazing! I love it so much!")
        assert result["sentiment"] == "positive"
        assert result["score"] > 0.05

    def test_negative_text(self):
        result = analyze_sentiment("This is terrible and awful, I hate it.")
        assert result["sentiment"] == "negative"
        assert result["score"] < -0.05

    def test_neutral_text(self):
        result = analyze_sentiment("The meeting is at 3pm.")
        assert result["sentiment"] == "neutral"
        assert -0.05 <= result["score"] <= 0.05

    def test_empty_string(self):
        result = analyze_sentiment("")
        assert result["sentiment"] == "neutral"
        assert result["score"] == 0.0

    def test_whitespace_only(self):
        result = analyze_sentiment("   ")
        assert result["sentiment"] == "neutral"
        assert result["score"] == 0.0

    def test_score_is_rounded(self):
        result = analyze_sentiment("Great product!")
        assert isinstance(result["score"], float)
        # Score should have at most 4 decimal places
        score_str = str(result["score"])
        if "." in score_str:
            assert len(score_str.split(".")[1]) <= 4
