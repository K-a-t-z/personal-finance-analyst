import pytest
from datetime import date
from decimal import Decimal

from app.utils.dates import parse_date
from app.utils.money import parse_amount


class TestParseDate:
    """Tests for parse_date function."""
    
    def test_valid_date(self):
        """Test parsing a valid date string."""
        result = parse_date("Sat, 24 May 2025")
        assert result == date(2025, 5, 24)
    
    def test_valid_date_with_whitespace(self):
        """Test parsing a date string with leading/trailing whitespace."""
        result = parse_date("  Sat, 24 May 2025  ")
        assert result == date(2025, 5, 24)
    
    def test_invalid_format(self):
        """Test that invalid date format raises ValueError."""
        with pytest.raises(ValueError, match="Failed to parse date"):
            parse_date("2025-05-24")
    
    def test_invalid_date_string(self):
        """Test that invalid date string raises ValueError."""
        with pytest.raises(ValueError, match="Failed to parse date"):
            parse_date("Invalid date")
    
    def test_empty_string(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Empty date string"):
            parse_date("")
    
    def test_whitespace_only(self):
        """Test that whitespace-only string raises ValueError."""
        with pytest.raises(ValueError, match="Empty date string"):
            parse_date("   ")
    
    def test_non_string_input(self):
        """Test that non-string input raises ValueError."""
        with pytest.raises(ValueError, match="Expected string"):
            parse_date(123)
        
        with pytest.raises(ValueError, match="Expected string"):
            parse_date(None)


class TestParseAmount:
    """Tests for parse_amount function."""
    
    def test_positive_with_dollar_sign(self):
        """Test parsing positive amount with dollar sign."""
        result = parse_amount("$6.15")
        assert result == Decimal("6.15")
    
    def test_negative_with_dollar_sign(self):
        """Test parsing negative amount with dollar sign."""
        result = parse_amount("-$10.00")
        assert result == Decimal("-10.00")
    
    def test_positive_without_dollar_sign(self):
        """Test parsing positive amount without dollar sign."""
        result = parse_amount("6.15")
        assert result == Decimal("6.15")
    
    def test_negative_without_dollar_sign(self):
        """Test parsing negative amount without dollar sign."""
        result = parse_amount("-10.00")
        assert result == Decimal("-10.00")
    
    def test_with_commas(self):
        """Test parsing amount with comma separators."""
        result = parse_amount("$1,234.56")
        assert result == Decimal("1234.56")
    
    def test_with_whitespace(self):
        """Test parsing amount with leading/trailing whitespace."""
        result = parse_amount("  $6.15  ")
        assert result == Decimal("6.15")
    
    def test_quantization(self):
        """Test that amounts are quantized to 2 decimal places."""
        result = parse_amount("$6.1")
        assert result == Decimal("6.10")
    
    def test_invalid_string(self):
        """Test that invalid amount string raises ValueError."""
        with pytest.raises(ValueError, match="Failed to parse amount"):
            parse_amount("not a number")
    
    def test_empty_string(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Empty amount string"):
            parse_amount("")
    
    def test_whitespace_only(self):
        """Test that whitespace-only string raises ValueError."""
        with pytest.raises(ValueError, match="Empty amount string"):
            parse_amount("   ")
    
    def test_only_symbols(self):
        """Test that string with only symbols raises ValueError."""
        with pytest.raises(ValueError, match="contains no numeric value"):
            parse_amount("$$$")
    
    def test_non_string_input(self):
        """Test that non-string input raises ValueError."""
        with pytest.raises(ValueError, match="Expected string"):
            parse_amount(123)
        
        with pytest.raises(ValueError, match="Expected string"):
            parse_amount(None)
