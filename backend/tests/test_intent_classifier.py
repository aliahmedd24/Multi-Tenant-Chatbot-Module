"""Tests for the intent classifier service."""

from app.services.intent_classifier import classify_intent


class TestClassifyIntent:
    """Tests for classify_intent function."""

    def test_greeting(self):
        assert classify_intent("Hello there!") == "greeting"
        assert classify_intent("Hi, how are you?") == "greeting"
        assert classify_intent("Good morning") == "greeting"

    def test_question(self):
        assert classify_intent("What are your hours?") == "question"
        assert classify_intent("How do I contact support?") == "question"

    def test_complaint(self):
        assert classify_intent("This service is terrible!") == "complaint"
        assert classify_intent("I am furious about the delay") == "complaint"

    def test_feedback(self):
        assert classify_intent("I suggest improving the checkout flow") == "feedback"
        assert classify_intent("I'd like to give some feedback") == "feedback"

    def test_order_inquiry(self):
        assert classify_intent("Where is my order?") == "order_inquiry"
        assert classify_intent("I want to track my delivery") == "order_inquiry"

    def test_other_fallback(self):
        assert classify_intent("lorem ipsum dolor sit amet") == "other"

    def test_case_insensitivity(self):
        assert classify_intent("HELLO") == "greeting"
        assert classify_intent("TERRIBLE service") == "complaint"

    def test_empty_string(self):
        assert classify_intent("") == "other"

    def test_whitespace_only(self):
        assert classify_intent("   ") == "other"

    def test_priority_order(self):
        # "Hello, this is terrible" - greeting should match first
        assert classify_intent("Hello, this is terrible") == "greeting"
