import pytest

from app.llm.orchestrator import classify_intent, extract_month


class TestClassifyIntent:
    """Tests for classify_intent function."""
    
    def test_monthly_summary_intent(self):
        """Test that 'How much did I spend in 2025-05?' is classified as monthly_summary."""
        question = "How much did I spend in 2025-05?"
        result = classify_intent(question)
        assert result == "monthly_summary"
    
    def test_category_breakdown_intent(self):
        """Test that 'Give category breakdown for 2025-05' is classified as category_breakdown."""
        question = "Give category breakdown for 2025-05"
        result = classify_intent(question)
        assert result == "category_breakdown"


class TestExtractMonth:
    """Tests for extract_month function."""
    
    def test_extract_month_finds_valid_month(self):
        """Test that extract_month finds '2025-05' in a question."""
        question = "How much did I spend in 2025-05?"
        result = extract_month(question)
        assert result == "2025-05"
    
    def test_extract_month_returns_none_when_no_month(self):
        """Test that extract_month returns None when no month is found."""
        question = "How much did I spend?"
        result = extract_month(question)
        assert result is None
