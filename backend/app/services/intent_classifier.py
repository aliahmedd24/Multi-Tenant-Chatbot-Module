"""Simple rule-based intent classification for customer messages.

Uses regex pattern matching for deterministic, zero-latency classification.
Ordered by priority - first match wins.
"""

import re

_INTENT_PATTERNS = [
    ("greeting", re.compile(
        r"\b(hi|hello|hey|good morning|good evening|good afternoon|marhaba|salam|ahlan)\b",
        re.IGNORECASE,
    )),
    ("complaint", re.compile(
        r"\b(complain|terrible|awful|worst|unacceptable|disgusted|angry|furious|horrible|pathetic|useless)\b",
        re.IGNORECASE,
    )),
    ("feedback", re.compile(
        r"\b(feedback|suggest|recommend|improve|opinion|review|wish|would be nice)\b",
        re.IGNORECASE,
    )),
    ("order_inquiry", re.compile(
        r"\b(order|delivery|track|shipping|package|arrived|dispatch|shipment|deliver)\b",
        re.IGNORECASE,
    )),
    ("question", re.compile(
        r"(\?|^(what|when|where|how|who|why|can you|do you|is there|could|does|are there|is it)\b)",
        re.IGNORECASE,
    )),
]


def classify_intent(text: str) -> str:
    """Classify the intent of a customer message.

    Returns one of: greeting, complaint, feedback, order_inquiry, question, other
    """
    if not text or not text.strip():
        return "other"

    for intent_label, pattern in _INTENT_PATTERNS:
        if pattern.search(text):
            return intent_label

    return "other"
