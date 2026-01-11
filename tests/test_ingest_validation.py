import pytest
import pandas as pd

from app.core.parsing import validate_columns, REQUIRED_COLUMNS


class TestValidateColumns:
    """Tests for validate_columns function."""
    
    def test_missing_one_column(self):
        """Test that validate_columns fails when one required column is missing."""
        # Create a DataFrame missing the "Category" column
        df = pd.DataFrame({
            "Date": ["Sat, 24 May 2025"],
            "Amount": ["$6.15"],
            "Where?": ["Store"],
            "What?": ["Purchase"],
            "Source": ["Credit Card"]
            # Missing "Category"
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_columns(df)
        
        # Verify the error message lists the missing column
        error_message = str(exc_info.value)
        assert "Missing required columns" in error_message
        assert "Category" in error_message
        assert "['Category']" in error_message or '"Category"' in error_message
    
    def test_all_columns_present(self):
        """Test that validate_columns passes when all required columns are present."""
        df = pd.DataFrame({
            "Date": ["Sat, 24 May 2025"],
            "Amount": ["$6.15"],
            "Where?": ["Store"],
            "What?": ["Purchase"],
            "Category": ["Food"],
            "Source": ["Credit Card"]
        })
        
        # Should not raise an exception
        validate_columns(df)
    
    def test_multiple_missing_columns(self):
        """Test that validate_columns lists all missing columns."""
        # Create a DataFrame missing multiple columns
        df = pd.DataFrame({
            "Date": ["Sat, 24 May 2025"],
            "Amount": ["$6.15"]
            # Missing "Where?", "What?", "Category", "Source"
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_columns(df)
        
        error_message = str(exc_info.value)
        assert "Missing required columns" in error_message
        # Verify multiple missing columns are listed
        assert "Where?" in error_message or "What?" in error_message
